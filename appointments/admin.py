from django.contrib import admin
from .models import DoctorAvailability, Appointment, EmergencyCase, AppointmentFeedback


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['veterinarian', 'day_of_week', 'start_time', 'end_time', 'is_available']
    list_filter = ['day_of_week', 'is_available']
    search_fields = ['veterinarian__username']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['pet', 'owner', 'veterinarian', 'appointment_date', 'appointment_time', 'status', 'is_emergency']
    list_filter = ['status', 'is_emergency', 'priority', 'appointment_date']
    search_fields = ['pet__name', 'owner__username', 'veterinarian__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'appointment_date'


@admin.register(EmergencyCase)
class EmergencyCaseAdmin(admin.ModelAdmin):
    list_display = ['pet', 'owner', 'severity', 'status', 'queue_number', 'reported_at']
    list_filter = ['severity', 'status', 'reported_at']
    search_fields = ['pet__name', 'owner__username', 'symptoms']
    readonly_fields = ['queue_number', 'reported_at', 'updated_at']
    date_hierarchy = 'reported_at'


@admin.register(AppointmentFeedback)
class AppointmentFeedbackAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'rating', 'would_recommend', 'created_at']
    list_filter = ['rating', 'would_recommend', 'created_at']
    readonly_fields = ['created_at']
