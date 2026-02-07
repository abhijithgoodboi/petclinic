from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='list'),
    path('book/', views.book_appointment, name='book'),
    path('<int:pk>/', views.appointment_detail, name='detail'),
    path('<int:pk>/cancel/', views.cancel_appointment, name='cancel'),
    path('<int:pk>/finish/', views.finish_appointment, name='finish'),
    path('emergency/resolve/<int:pk>/', views.resolve_emergency, name='resolve_emergency'),
    path('availability/', views.doctor_availability, name='availability'),
    path('availability/manage/', views.manage_availability, name='manage_availability'),
    path('availability/delete/<int:pk>/', views.delete_availability, name='delete_availability'),
    path('availability/check/', views.check_availability, name='check_availability'),
    path('availability/schedule/', views.get_doctor_schedule, name='get_doctor_schedule'),
    path('emergency/', views.emergency_cases, name='emergency'),
    path('emergency/claim/<int:pk>/', views.claim_emergency, name='claim_emergency'),
    
    # Queue & Token System
    path('queue/', views.queue_status, name='queue_status'),
    path('queue/api/', views.queue_api, name='queue_api'),
    path('check-in/<int:pk>/', views.check_in, name='check_in'),
    path('call-next/', views.call_next_patient, name='call_next'),
    
    # Doctor Status
    path('doctors/status/', views.doctor_status_view, name='doctor_status'),
    path('doctors/update-status/', views.update_doctor_status, name='update_doctor_status'),
    
    # Grooming
    path('grooming/', views.grooming_list, name='grooming_list'),
    path('grooming/services/', views.grooming_services, name='grooming_services'),
    path('grooming/book/', views.book_grooming, name='book_grooming'),
    path('grooming/<int:pk>/cancel/', views.cancel_grooming, name='cancel_grooming'),
    
    # AI Bridge API Endpoints
    path('api/analyze-symptoms/', views.api_analyze_symptoms, name='api_analyze_symptoms'),
    path('api/analyze-image/', views.api_analyze_image, name='api_analyze_image'),
    path('api/check-priority/', views.api_check_priority, name='api_check_priority'),
]
