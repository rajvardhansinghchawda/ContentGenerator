from rest_framework import serializers
from .models import Teacher

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = [
            'id', 'email', 'full_name', 'profile_pic', 'department', 'institution', 
            'header_image_id', 'footer_image_id', 'default_session', 'default_semester',
            'default_subject_name', 'default_subject_code', 'is_profile_setup', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'created_at']
