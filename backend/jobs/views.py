import logging

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Job, Subject
from .serializers import (JobCreateSerializer, JobDetailSerializer, JobStatusSerializer, SubjectSerializer)
from .tasks import generate_content_task


logger = logging.getLogger(__name__)


def _enqueue_generation_job(job: Job) -> bool:
    try:
        generate_content_task.delay(str(job.id))
        return True
    except Exception:
        logger.exception("Failed to enqueue job %s", job.id)
        job.status = Job.STATUS_FAILED
        job.error_message = 'Background worker is unavailable. Start Redis/Celery and try again.'
        job.save(update_fields=['status', 'error_message'])
        return False


class SubjectListCreateView(generics.ListCreateAPIView):
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Subject.objects.filter(teacher=self.request.user)
    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


class SubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Subject.objects.filter(teacher=self.request.user)


class JobCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = JobCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        job = serializer.save(teacher=request.user)
        enqueued = _enqueue_generation_job(job)
        return Response(
            {
                'job_id': str(job.id),
                'id': str(job.id),
                'status': job.status,
                'enqueued': enqueued,
                'error_message': job.error_message,
            },
            status=status.HTTP_201_CREATED,
        )


class JobListView(generics.ListAPIView):
    serializer_class = JobDetailSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        qs = Job.objects.filter(teacher=self.request.user)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class JobDetailView(generics.RetrieveAPIView):
    serializer_class = JobDetailSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Job.objects.filter(teacher=self.request.user)


class JobStatusView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        try:
            job = Job.objects.get(id=pk, teacher=request.user)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(JobStatusSerializer(job).data)


class JobRegenerateView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        try:
            job = Job.objects.get(id=pk, teacher=request.user)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)
        if job.status == Job.STATUS_PROCESSING:
            return Response({'error': 'Job is already processing.'}, status=status.HTTP_400_BAD_REQUEST)
        
        job.status = Job.STATUS_PENDING
        job.error_message = ''
        job.pre_doc_url = ''
        job.post_doc_url = ''
        job.quiz_form_url = ''
        job.completed_at = None
        job.save()

        enqueued = _enqueue_generation_job(job)
        return Response(
            {
                'job_id': str(job.id),
                'id': str(job.id),
                'status': job.status,
                'enqueued': enqueued,
                'error_message': job.error_message,
            }
        )
