"""
Celery tasks for content generation.
Main task: generate_content_task
"""
import logging
import time

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def generate_content_task(self, job_id: str):
    """
    Main Celery task that orchestrates the full content generation pipeline:
    1. Build prompts
    2. Call Groq AI
    3. Validate content
    4. Push to Google Docs + Forms
    5. Update job status
    """
    from jobs.models import Job
    from ai_engine.prompt_builder import build_docs_prompt, build_quiz_prompt

    from ai_engine.groq_client import call_groq
    from ai_engine.validators import validate_content
    from google_services.auth_manager import build_docs_service, build_forms_service, build_drive_service
    from google_services.docs_creator import create_pre_doc, create_post_doc
    from google_services.forms_creator import create_quiz_form

    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        logger.error(f"Job {job_id} not found")
        return

    job.status = Job.STATUS_PROCESSING
    job.save(update_fields=['status'])

    start_time = time.time()

    try:
        from ai_engine.groq_client import verify_prompt_safety
        logger.info(f"[Job {job_id}] Starting generation pipeline...")
        
        # Combine topic and notes for a thorough check
        job.current_step = "Safety Check: Scanning topic..."
        job.save(update_fields=['current_step'])
        
        # Combine topic and notes for a thorough check
        safety_text = f"Topic: {job.topic} | Notes: {job.additional_notes}"
        if not verify_prompt_safety(safety_text, model='llama-guard-3-8b'):
            logger.warning(f"[Job {job_id}] Prompt flagged as malicious!")
            raise PermissionError("Safety Check Failed: The provided topic or instructions violated our content policy.")

        # ── Step 2: Phase 1 - Generate Docs ────────────────────────
        job.current_step = "Phase 1: Generating Lecture Notes (using Mixtral)..."
        job.save(update_fields=['current_step'])

        # Use a high-quality model for notes
        logger.info(f"[Job {job_id}] Calling Groq Phase 1 (Docs)...")

        docs_prompt = build_docs_prompt(job)
        docs_res = call_groq(
            docs_prompt['system'], 
            docs_prompt['user'], 
            preferred_model='llama-3.3-70b-versatile',
            max_tokens=2500
        )
        
        # ── Step 2.5: Phase 2 - Generate Quiz ──────────────────────
        job.current_step = f"Phase 2: Building {job.num_questions}-Question Quiz (using Llama)..."
        job.save(update_fields=['current_step'])

        # Use the "instant" model for the large quiz array
        logger.info(f"[Job {job_id}] Calling Groq Phase 2 (Quiz)...")
        quiz_prompt = build_quiz_prompt(job)
        quiz_res = call_groq(
            quiz_prompt['system'], 
            quiz_prompt['user'], 
            preferred_model='llama-3.1-8b-instant',
            max_tokens=3500
        )

        # Merge results
        content = {
            'pre_doc': docs_res['content']['pre_doc'],
            'post_doc': docs_res['content']['post_doc'],
            'quiz': quiz_res['content']['quiz']
        }
        tokens_used = (docs_res.get('tokens_used') or 0) + (quiz_res.get('tokens_used') or 0)
        model_used = docs_res['model_used']


        # ── Step 3: Validate ───────────────────────────────────────
        logger.info(f"[Job {job_id}] Validating content...")
        content = validate_content(content, job.num_questions)

        # ── Step 4: Push to Google ─────────────────────────────────
        job.current_step = "Phase 3: Creating Google Documents..."
        job.save(update_fields=['current_step'])

        teacher = job.teacher
        docs_svc  = build_docs_service(teacher)
        forms_svc = build_forms_service(teacher)
        drive_svc = build_drive_service(teacher)

        logger.info(f"[Job {job_id}] Creating pre-doc...")
        pre_doc_id, pre_doc_url = create_pre_doc(docs_svc, drive_svc, content['pre_doc'], job)

        logger.info(f"[Job {job_id}] Creating post-doc...")
        post_doc_id, post_doc_url = create_post_doc(docs_svc, drive_svc, content['post_doc'], job)

        logger.info(f"[Job {job_id}] Creating quiz form...")
        job.current_step = "Phase 4: Setting up Quiz Form..."
        job.save(update_fields=['current_step'])

        quiz_form_id, quiz_form_url = create_quiz_form(forms_svc, drive_svc, content['quiz'])

        # ── Step 5: Update job ─────────────────────────────────────
        elapsed = time.time() - start_time

        job.status              = Job.STATUS_COMPLETED
        job.pre_doc_id          = pre_doc_id
        job.pre_doc_url         = pre_doc_url
        job.post_doc_id         = post_doc_id
        job.post_doc_url        = post_doc_url
        job.quiz_form_id        = quiz_form_id
        job.quiz_form_url       = quiz_form_url
        job.tokens_used         = tokens_used
        job.model_used          = model_used
        job.generation_time_sec = round(elapsed, 2)
        job.completed_at        = timezone.now()
        job.save()

        logger.info(f"[Job {job_id}] Completed in {elapsed:.1f}s")

    except Exception as exc:
        elapsed = time.time() - start_time
        logger.error(f"[Job {job_id}] Failed after {elapsed:.1f}s: {exc}", exc_info=True)
        job.status = Job.STATUS_FAILED
        job.error_message = str(exc)
        job.generation_time_sec = round(elapsed, 2)
        job.save(update_fields=['status', 'error_message', 'generation_time_sec'])

        # Permission/access-denied failures are permanent; retries only waste queue time.
        if isinstance(exc, PermissionError):
            return

        raise self.retry(exc=exc, countdown=60)
