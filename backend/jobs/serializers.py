from rest_framework import serializers
from .models import Job, Subject


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'class_name', 'semester', 'created_at']
        read_only_fields = ['id', 'created_at']


class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['topic', 'subtopics', 'difficulty', 'num_questions', 'marks_per_question', 'question_type', 'language', 'additional_notes', 'subject',]

    def validate_num_questions(self, value):
        if not (1 <= value <= 100):
            raise serializers.ValidationError('Number of questions must be between 1 and 100.')
        return value


    def validate_marks_per_question(self, value):
        if value <= 0:
            raise serializers.ValidationError('Marks per question must be positive.')
        return value


class JobStatusSerializer(serializers.ModelSerializer):
    quiz_url = serializers.CharField(source='quiz_form_url', read_only=True)

    class Meta:
        model = Job
        fields = ['id', 'status', 'error_message', 'pre_doc_url', 'post_doc_url', 'quiz_form_url', 'quiz_url', 'generation_time_sec', 'tokens_used']


class JobDetailSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True, default=None)
    total_marks  = serializers.ReadOnlyField()
    quiz_url = serializers.CharField(source='quiz_form_url', read_only=True)

    class Meta:
        model = Job
        fields = ['id', 'topic', 'subtopics', 'difficulty', 'num_questions', 'marks_per_question', 'total_marks', 'question_type', 'language', 'additional_notes', 'subject', 'subject_name', 'status', 'error_message', 'pre_doc_url', 'post_doc_url', 'quiz_form_url', 'quiz_url', 'tokens_used', 'model_used', 'generation_time_sec', 'created_at', 'completed_at',]
        read_only_fields = fields
