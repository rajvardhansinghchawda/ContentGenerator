import uuid
from django.db import models
from auth_app.models import Teacher


class Subject(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher    = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='subjects')
    name       = models.CharField(max_length=255)
    code       = models.CharField(max_length=50, blank=True)
    class_name = models.CharField(max_length=100, blank=True)
    semester   = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subjects'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Job(models.Model):
    STATUS_PENDING    = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED  = 'completed'
    STATUS_FAILED     = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING,'Pending'),
        (STATUS_PROCESSING,'Processing'),
        (STATUS_COMPLETED,'Completed'),
        (STATUS_FAILED,'Failed'),
    ]
    DIFFICULTY_CHOICES = [
        ('easy','Easy'),
        ('medium','Medium'),
        ('hard','Hard'),
    ]
    QUESTION_TYPE_CHOICES = [
        ('MCQ','Multiple Choice'),
        ('SHORT','Short Answer'),
        ('MIXED','Mixed'),
    ]

    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='jobs')
    subject = models.ForeignKey(Subject, null=True, blank=True, on_delete=models.SET_NULL, related_name='jobs')

    topic               = models.TextField()
    subtopics           = models.TextField(blank=True)
    difficulty          = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    num_questions       = models.PositiveIntegerField(default=10)
    marks_per_question  = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    question_type       = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='MCQ')
    language            = models.CharField(max_length=50, default='English')
    additional_notes    = models.TextField(blank=True)

    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.TextField(blank=True)
    current_step  = models.CharField(max_length=255, blank=True, help_text="Current stage of generation (Docs, Quiz, etc.)")


    pre_doc_url   = models.URLField(blank=True)
    post_doc_url  = models.URLField(blank=True)
    quiz_form_url = models.URLField(blank=True)
    pre_doc_id    = models.CharField(max_length=255, blank=True)
    post_doc_id   = models.CharField(max_length=255, blank=True)
    quiz_form_id  = models.CharField(max_length=255, blank=True)

    tokens_used          = models.IntegerField(null=True, blank=True)
    model_used           = models.CharField(max_length=100, blank=True)
    generation_time_sec  = models.FloatField(null=True, blank=True)

    created_at   = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.topic[:50]} — {self.status}"

    @property
    def total_marks(self):
        return float(self.marks_per_question) * self.num_questions
