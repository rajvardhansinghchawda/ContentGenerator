import logging
from datetime import timezone

from django.conf import settings
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from .models import Teacher
from .token_utils import encrypt_token
from .serializers import TeacherSerializer

logger = logging.getLogger(__name__)


def _build_flow():
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    return Flow.from_client_config(client_config, scopes=settings.GOOGLE_SCOPES, redirect_uri=settings.GOOGLE_REDIRECT_URI)


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        flow = _build_flow()
        auth_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
        request.session['oauth_state'] = state
        # Keep both keys for backward compatibility with different frontend builds.
        return Response({'auth_url': auth_url, 'url': auth_url})


class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get('code')
        if not code:
            return redirect(f"{settings.FRONTEND_URL}/?error=no_code")
        try:
            flow = _build_flow()
            flow.fetch_token(code=code)
            credentials = flow.credentials
            user_info_service = build('oauth2', 'v2', credentials=credentials)
            user_info = user_info_service.userinfo().get().execute()
            email = user_info.get('email')
            if not email:
                return redirect(f"{settings.FRONTEND_URL}/?error=no_email")
            
            expiry = credentials.expiry.replace(tzinfo=timezone.utc) if credentials.expiry else None
            
            teacher, _ = Teacher.objects.update_or_create(
                email=email, 
                defaults={
                    'google_id': user_info.get('id'), 
                    'full_name': user_info.get('name', ''), 
                    'profile_pic': user_info.get('picture', ''),
                    'token_expiry': expiry
                }
            )
            
            teacher._access_token = encrypt_token(credentials.token or '')
            if credentials.refresh_token:
                teacher._refresh_token = encrypt_token(credentials.refresh_token)
            teacher.save()
            
            request.session['teacher_id'] = str(teacher.id)
            request.session.modified = True
            
            return redirect(f"{settings.FRONTEND_URL}/dashboard")
        except Exception as e:
            logger.error(f"OAuth callback error: {e}", exc_info=True)
            return redirect(f"{settings.FRONTEND_URL}/?error=auth_failed")


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(TeacherSerializer(request.user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        request.session.flush()
        return Response({'message': 'Logged out successfully.'})
