from django.urls import path
from . import views

urlpatterns = [
    path('google/login/', views.GoogleLoginView.as_view(), name='google-login'),
    path('google/callback/', views.GoogleCallbackView.as_view(), name='google-callback'),
    path('me/', views.MeView.as_view(), name='me'),
    path('asset-upload/', views.AssetUploadView.as_view(), name='asset-upload'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]
