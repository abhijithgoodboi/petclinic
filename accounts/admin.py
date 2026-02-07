from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, VeterinarianProfile, PetOwnerProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone_number', 'address', 'date_of_birth', 'profile_picture', 'is_active_account')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone_number', 'email')
        }),
    )


@admin.register(VeterinarianProfile)
class VeterinarianProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'license_number', 'specialization', 'years_of_experience', 'rating', 'available_for_emergency']
    list_filter = ['available_for_emergency', 'specialization']
    search_fields = ['user__username', 'user__email', 'license_number', 'specialization']
    readonly_fields = ['total_consultations', 'created_at', 'updated_at']


@admin.register(PetOwnerProfile)
class PetOwnerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'emergency_contact_name', 'emergency_contact_phone', 'preferred_vet']
    search_fields = ['user__username', 'user__email', 'emergency_contact_name']
    autocomplete_fields = ['preferred_vet']
