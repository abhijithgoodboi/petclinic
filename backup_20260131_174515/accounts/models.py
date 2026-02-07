from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class User(AbstractUser):
    """Extended User model with role-based access"""
    
    USER_ROLES = (
        ('ADMIN', 'Administrator'),
        ('VET', 'Veterinarian'),
        ('OWNER', 'Pet Owner'),
    )
    
    role = models.CharField(max_length=20, choices=USER_ROLES, default='OWNER')
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_active_account = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_joined']
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    @property
    def is_veterinarian(self):
        return self.role == 'VET'
    
    @property
    def is_pet_owner(self):
        return self.role == 'OWNER'


class VeterinarianProfile(models.Model):
    """Additional information specific to veterinarians"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vet_profile')
    license_number = models.CharField(max_length=100, unique=True)
    specialization = models.CharField(max_length=200)
    years_of_experience = models.IntegerField(default=0)
    qualifications = models.TextField()
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bio = models.TextField(blank=True)
    available_for_emergency = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_consultations = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-rating', 'user__first_name']
        
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialization}"


class PetOwnerProfile(models.Model):
    """Additional information for pet owners"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owner_profile')
    emergency_contact_name = models.CharField(max_length=200)
    emergency_contact_phone = models.CharField(max_length=17)
    preferred_vet = models.ForeignKey(
        VeterinarianProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='preferred_by'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"
