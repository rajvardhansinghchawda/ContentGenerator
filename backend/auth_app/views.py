import logging
from datetime import timezone
from django.conf import settings
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

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


@method_decorator(csrf_exempt, name='dispatch')
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logger.info(f"GoogleLoginView.get called. Session ID: {request.session.session_key}")
        try:
            flow = _build_flow()
            auth_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
            request.session['oauth_state'] = state
            logger.info(f"Generated auth_url. State saved to session: {state}")
            return Response({'auth_url': auth_url, 'url': auth_url})
        except Exception as e:
            logger.error(f"Error in GoogleLoginView: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            
            teacher, created = Teacher.objects.get_or_create(email=email)
            
            # Update core identifies and credentials
            teacher.google_id = user_info.get('id')
            teacher.token_expiry = expiry
            
            # Only set name/pic if they are currently empty (first time or never set)
            if not teacher.full_name:
                teacher.full_name = user_info.get('name', '')
            if not teacher.profile_pic:
                teacher.profile_pic = user_info.get('picture', '')
            
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

    def patch(self, request):
        serializer = TeacherSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssetUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file_obj = request.FILES.get('file')
        asset_type = request.data.get('type') # 'header' or 'footer'
        
        if not file_obj or asset_type not in ['header', 'footer']:
            return Response({'error': 'Missing file or invalid type.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from google_services.auth_manager import build_drive_service
            drive_service = build_drive_service(request.user)

            # 1. Upload to Google Drive
            file_metadata = {
                'name': f'eduflow_{asset_type}_{request.user.id}',
                'parents': [] # Root for now
            }
            media = MediaIoBaseUpload(file_obj, mimetype=file_obj.content_type, resumable=True)
            uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            file_id = uploaded_file.get('id')

            # 2. Set permissions so the Doc can access it (anyone with link can view)
            drive_service.permissions().create(
                fileId=file_id,
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()

            # 3. Update Teacher model
            if asset_type == 'header':
                request.user.header_image_id = file_id
            else:
                request.user.footer_image_id = file_id
            request.user.save()

            return Response({
                'message': f'{asset_type.capitalize()} asset uploaded successfully.',
                'file_id': file_id
            })
        except Exception as e:
            logger.error(f"Asset upload failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        request.session.flush()
        return Response({'message': 'Logged out successfully.'})
