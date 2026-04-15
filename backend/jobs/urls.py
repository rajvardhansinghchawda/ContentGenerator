from django.urls import path
from . import views

urlpatterns = [
    path('jobs/create/', views.JobCreateView.as_view(), name='job-create'),
    path('jobs/', views.JobListView.as_view(), name='job-list'),
    path('jobs/<uuid:pk>/', views.JobDetailView.as_view(), name='job-detail'),
    path('jobs/<uuid:pk>/status/', views.JobStatusView.as_view(), name='job-status'),
    path('jobs/<uuid:pk>/regenerate/', views.JobRegenerateView.as_view(), name='job-regenerate'),
    path('subjects/', views.SubjectListCreateView.as_view(), name='subject-list-create'),
    path('subjects/<uuid:pk>/', views.SubjectDetailView.as_view(), name='subject-detail'),
]
