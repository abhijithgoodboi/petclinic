"""
Main URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Social Authentication (allauth)
    path('auth/', include('allauth.urls')),
    
    # Apps
    path('accounts/', include('accounts.urls')),
    path('appointments/', include('appointments.urls')),
    path('medical/', include('medical_records.urls')),
    path('ai-diagnosis/', include('ai_diagnosis.urls')),
    
    # Static pages
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    path('about/', views.about, name='about'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "Veterinary Workflow Administration"
admin.site.site_title = "Vet Workflow Admin"
admin.site.index_title = "Welcome to Veterinary Workflow Management"
