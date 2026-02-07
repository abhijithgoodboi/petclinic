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
]
