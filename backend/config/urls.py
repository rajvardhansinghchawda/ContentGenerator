from django.contrib import admin
from django.urls import path, include
from .views import health_check

urlpatterns = [
    path('', health_check, name='root-health'),
    path('health/', health_check, name='health'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('auth_app.urls')),
    path('api/', include('jobs.urls')),
]
