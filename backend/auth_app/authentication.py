from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from auth_app.models import Teacher

class SessionTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        teacher_id = request.session.get('teacher_id')
        if not teacher_id:
            return None
        try:
            teacher = Teacher.objects.get(id=teacher_id, is_active=True)
            return (teacher, None)
        except Teacher.DoesNotExist:
            raise AuthenticationFailed('Teacher not found or inactive.')
