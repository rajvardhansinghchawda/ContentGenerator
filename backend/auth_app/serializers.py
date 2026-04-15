from rest_framework import serializers
from .models import Teacher

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'email', 'full_name', 'profile_pic', 'created_at']
        read_only_fields = fields
