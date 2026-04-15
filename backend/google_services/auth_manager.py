"""
Manages Google OAuth credentials — refresh and build service objects.
"""
import logging
from datetime import timezone

from django.utils import timezone as dj_timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from django.conf import settings
from auth_app.token_utils import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)


def get_credentials(teacher) -> Credentials:
    """
    Returns valid Google credentials for a teacher, refreshing if needed.
    """
    creds = Credentials(
        token=decrypt_token(teacher._access_token),
        refresh_token=decrypt_token(teacher._refresh_token),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=settings.GOOGLE_SCOPES,
    )

    # Check if expired and refresh
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Update stored tokens
            teacher._access_token = encrypt_token(creds.token)
            if creds.expiry:
                teacher.token_expiry = creds.expiry.replace(tzinfo=timezone.utc)
            teacher.save(update_fields=['_access_token', 'token_expiry', 'updated_at'])
            logger.info(f"Refreshed Google token for {teacher.email}")
        except Exception as e:
            logger.error(f"Failed to refresh token for {teacher.email}: {e}")
            raise

    return creds


def build_docs_service(teacher):
    return build('docs', 'v1', credentials=get_credentials(teacher))


def build_forms_service(teacher):
    return build('forms', 'v1', credentials=get_credentials(teacher))


def build_drive_service(teacher):
    return build('drive', 'v3', credentials=get_credentials(teacher))
