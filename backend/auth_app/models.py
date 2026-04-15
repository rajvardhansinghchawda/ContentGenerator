import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class TeacherManager(BaseUserManager):
    def create_user(self, email, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user


class Teacher(AbstractBaseUser, PermissionsMixin):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email         = models.EmailField(unique=True)
    full_name     = models.CharField(max_length=255, blank=True)
    google_id     = models.CharField(max_length=255, unique=True, null=True, blank=True)
    profile_pic   = models.URLField(blank=True)
    _access_token  = models.TextField(blank=True, db_column='access_token')
    _refresh_token = models.TextField(blank=True, db_column='refresh_token')
    token_expiry   = models.DateTimeField(null=True, blank=True)
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = TeacherManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'teachers'
        verbose_name = 'Teacher'

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.full_name or self.email
