from django.conf import settings

def _get_fernet():
    from cryptography.fernet import Fernet
    key = settings.TOKEN_ENCRYPTION_KEY
    if not key:
        # Fallback for development if key is missing
        key = Fernet.generate_key().decode()
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)

def encrypt_token(token: str) -> str:
    if not token:
        return ''
    return _get_fernet().encrypt(token.encode()).decode()

def decrypt_token(encrypted: str) -> str:
    if not encrypted:
        return ''
    try:
        return _get_fernet().decrypt(encrypted.encode()).decode()
    except Exception:
        return ''
