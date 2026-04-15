"""
PromptBuilderAgent — Constructs the prompts for Groq AI.
Now supports multi-phase generation to stay within token limits.
"""

def _get_job_context(job) -> str:
    subject_info = ""
    if job.subject:
        subject_info = f"Subject: {job.subject.name}"
        if job.subject.code:
            subject_info += f" ({job.subject.code})"
        if job.subject.class_name:
            subject_info += f" | Class: {job.subject.class_name}"
        if job.subject.semester:
            subject_info += f" | Semester: {job.subject.semester}"
    
    subtopics_info = ""
    if job.subtopics:
        subtopics_info = f"\nSubtopics to cover: {job.subtopics}"

    notes_info = ""
    if job.additional_notes:
        notes_info = f"\nAdditional instructions: {job.additional_notes}"
    
    context = f"""Topic: {job.topic}{subtopics_info}
{subject_info}
Difficulty: {job.difficulty.capitalize()}
Language: {job.language}
{notes_info}"""
    return context

def _get_system_prompt() -> str:
    return """You are an experienced university professor and academic content writer specializing in engineering and science education. You write detailed, classroom-ready educational content that mirrors how a skilled teacher actually explains concepts — not just defining terms, but building understanding step by step.
When generating content, you must follow these principles:
TEACHING STYLE: Write as if you are directly addressing students in a lecture or textbook. Use phrases like "Let us understand...", "Consider the following example...", "Notice that...", "It is important to remember that...", "This concept is fundamental because...". Break down complex ideas into digestible parts before building back up to the full picture.
DEPTH AND LENGTH: Every response must be comprehensive and detailed. This means each topic must include a thorough introduction and motivation for why the concept matters, a detailed explanation of the theory with derivations or reasoning where applicable, worked examples with clearly narrated step-by-step solutions, common misconceptions students have and how to correct them, real-world applications and analogies that make abstract ideas concrete, and a summary that reinforces the key takeaways.
STRUCTURE: Organize content with clear headings, subheadings, numbered explanations, and labeled examples. Use transitional sentences between sections to maintain the natural flow of a lecture or textbook chapter.
TONE: Encouraging, precise, and academic. Avoid being overly casual, but also avoid dry, dictionary-style definitions. Your goal is clarity and engagement.
OUTPUT FORMAT: You always respond with ONLY valid JSON and nothing else — no markdown, no preamble, no explanation outside the JSON structure. All the rich teaching content described above must be embedded inside the appropriate JSON fields."""

def build_docs_prompt(job) -> dict:
    """
    Returns a prompt focused ONLY on pre_doc and post_doc.
    """
    context = _get_job_context(job)
    user_prompt = f"""Generate the lecture notes (Pre-Lecture and Post-Lecture) for the following topic. Return ONLY a valid JSON object.

{context}

Return ONLY this JSON structure (no markdown, no extra text):
{{
  "pre_doc": {{
    "title": "Pre-Lecture Notes: {job.topic}",
    "learning_objectives": ["objective 1", "objective 2", "objective 3"],
    "prerequisite_topics": ["topic 1", "topic 2"],
    "introduction": "2-3 paragraph introduction to the topic",
    "key_concepts": [
      {{"concept": "Concept Name", "brief_explanation": "1-2 sentence explanation"}}
    ],
    "pre_reading_material": "2-3 paragraphs of background material students should review",
    "expected_outcomes": ["outcome 1", "outcome 2", "outcome 3"]
  }},
  "post_doc": {{
    "title": "Post-Lecture Notes: {job.topic}",
    "lecture_summary": "3-4 paragraph comprehensive summary of the lecture",
    "detailed_notes": [
      {{"heading": "Section Heading", "content": "Detailed content for this section"}}
    ],
    "key_formulas_or_definitions": ["Definition 1: ...", "Formula 2: ..."],
    "common_mistakes": ["Mistake 1 to avoid", "Mistake 2 to avoid"],
    "further_reading": ["Reference 1", "Reference 2"],
    "practice_problems": ["Problem 1", "Problem 2", "Problem 3", "Problem 4", "Problem 5"]
  }}
}}
Do not use any emojis in the content generation."""

    return {"system": _get_system_prompt(), "user": user_prompt}

def build_quiz_prompt(job) -> dict:
    """
    Returns a prompt focused ONLY on the quiz.
    """
    context = _get_job_context(job)
    user_prompt = f"""Generate an assessment quiz for the following topic. Return ONLY a valid JSON object.

{context}
Number of quiz questions: {job.num_questions}
Marks per question: {float(job.marks_per_question)}
Question type: {job.question_type}

Return ONLY this JSON structure (no markdown, no extra text):
{{
  "quiz": {{
    "title": "Quiz: {job.topic}",
    "total_marks": {int(job.num_questions * float(job.marks_per_question))},
    "questions": [
      {{
        "question_text": "Question text here?",
        "type": "{job.question_type if job.question_type != 'MIXED' else 'MCQ'}",
        "options": ["A) Option A", "B) Option B", "C) Option C", "D) Option D"],
        "correct_answer": "B",
        "explanation": "Why B is correct",
        "marks": {float(job.marks_per_question)}
      }}
    ]
  }}
}}

Ensure the quiz has exactly {job.num_questions} questions. NO MORE, NO LESS. 
CRITICAL: You MUST provide exactly {job.num_questions} question objects in the 'questions' array.
For MCQ questions, include exactly 4 options. 
CRITICAL: Do not always make the first option (A) the correct answer. Randomize the position of the correct answer (A, B, C, or D) across all questions.
For SHORT questions, set options to [] and correct_answer to a brief answer string.
Do not use any emojis in the content generation."""

    return {"system": _get_system_prompt(), "user": user_prompt}

def build_combined_prompt(job) -> dict:
    """Deprecated: Use build_docs_prompt and build_quiz_prompt instead."""
    # Keeping for compatibility if needed elsewhere temporarily
    context = _get_job_context(job)
    user_prompt = f"""Generate complete educational content for the following lecture. Return ONLY a valid JSON object.

{context}
Number of quiz questions: {job.num_questions}
{notes_info if hasattr(job, 'notes_info') else ''}

Return ONLY this JSON structure (no markdown, no extra text):
{{
  "pre_doc": {{ "title": "...", ... }},
  "post_doc": {{ "title": "...", ... }},
  "quiz": {{ "title": "...", ... }}
}}"""
    return {"system": _get_system_prompt(), "user": user_prompt}
