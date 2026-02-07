from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from medical_records.models import Pet
from datetime import datetime, timedelta

class DoctorAvailability(models.Model):
    """Doctor's availability schedule"""
    
    DAYS_OF_WEEK = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    veterinarian = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availabilities',
        limit_choices_to={'role': 'VET'}
    )
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    max_appointments = models.IntegerField(default=16, help_text="Maximum appointments per day")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'day_of_week', 'start_time']
        verbose_name_plural = 'Doctor availabilities'
        
    def __str__(self):
        if self.date:
            return f"Dr. {self.veterinarian.get_full_name()} - {self.date} ({self.start_time}-{self.end_time})"
        return f"Dr. {self.veterinarian.get_full_name()} - {self.get_day_of_week_display()} ({self.start_time}-{self.end_time})"
    
    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")


class Appointment(models.Model):
    """Appointment booking model"""
    
    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('CONFIRMED', 'Confirmed'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    )
    
    PRIORITY_LEVELS = (
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('EMERGENCY', 'Emergency'),
    )
    
    # Basic info
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='appointments')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments_as_owner'
    )
    veterinarian = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='appointments_as_vet',
        limit_choices_to={'role': 'VET'}
    )
    
    # Appointment details
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    duration = models.IntegerField(default=30, help_text="Duration in minutes")
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='NORMAL')
    is_emergency = models.BooleanField(default=False)
    
    # Visit details
    reason = models.TextField(help_text="Reason for visit")
    notes = models.TextField(blank=True)
    
    # Confirmation
    confirmation_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='appointments_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
        indexes = [
            models.Index(fields=['appointment_date', 'appointment_time']),
            models.Index(fields=['status']),
            models.Index(fields=['is_emergency']),
        ]
        
    def __str__(self):
        return f"{self.pet.name} - {self.appointment_date} at {self.appointment_time}"
    
    def clean(self):
        """Validate appointment data"""
        # Convert to timezone-aware datetime for comparison
        try:
            # Combine date and time
            appointment_datetime = datetime.combine(self.appointment_date, self.appointment_time)
            
            # Make timezone aware
            if timezone.is_naive(appointment_datetime):
                appointment_datetime = timezone.make_aware(appointment_datetime)
            
            # Check if appointment is in the past (only for new appointments)
            if not self.pk and appointment_datetime < timezone.now():
                raise ValidationError("Cannot book appointments in the past")
            
            # Check for overlapping appointments
            if self.veterinarian:
                overlapping = Appointment.objects.filter(
                    veterinarian=self.veterinarian,
                    appointment_date=self.appointment_date,
                    appointment_time=self.appointment_time,
                    status__in=['SCHEDULED', 'CONFIRMED', 'IN_PROGRESS']
                ).exclude(pk=self.pk if self.pk else None)
                
                if overlapping.exists():
                    raise ValidationError("This time slot is already booked")
        except (ValueError, TypeError) as e:
            # Handle date/time conversion errors
            raise ValidationError(f"Invalid date or time format: {str(e)}")
    
    def save(self, *args, **kwargs):
        # Automatically set priority for emergency cases
        if self.is_emergency:
            self.priority = 'EMERGENCY'
        
        # Calculate end time
        if not self.end_time and self.appointment_time:
            start = datetime.combine(self.appointment_date, self.appointment_time)
            end = start + timedelta(minutes=self.duration)
            self.end_time = end.time()
        
        super().save(*args, **kwargs)
    
    @property
    def is_upcoming(self):
        """Check if appointment is in the future"""
        try:
            appointment_datetime = datetime.combine(self.appointment_date, self.appointment_time)
            if timezone.is_naive(appointment_datetime):
                appointment_datetime = timezone.make_aware(appointment_datetime)
            return appointment_datetime > timezone.now()
        except:
            return False
    
    @property
    def is_today(self):
        """Check if appointment is today"""
        return self.appointment_date == timezone.now().date()


class EmergencyCase(models.Model):
    """Track emergency cases for priority handling"""
    
    SEVERITY_LEVELS = (
        ('CRITICAL', 'Critical'),
        ('SEVERE', 'Severe'),
        ('MODERATE', 'Moderate'),
        ('MILD', 'Mild'),
    )
    
    STATUS_CHOICES = (
        ('WAITING', 'Waiting'),
        ('IN_TREATMENT', 'In Treatment'),
        ('STABILIZED', 'Stabilized'),
        ('RESOLVED', 'Resolved'),
        ('REFERRED', 'Referred'),
    )
    
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='emergency_case',
        null=True,
        blank=True
    )
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='emergency_cases')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='emergency_cases_as_owner'
    )
    
    # Emergency details
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    symptoms = models.TextField()
    situation_description = models.TextField()
    
    # Treatment
    assigned_vet = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_cases_assigned',
        limit_choices_to={'role': 'VET'}
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='WAITING')
    treatment_started_at = models.DateTimeField(null=True, blank=True)
    treatment_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Priority queue
    queue_number = models.IntegerField(null=True, blank=True)
    wait_time_minutes = models.IntegerField(default=0)
    
    # Notes
    triage_notes = models.TextField(blank=True)
    treatment_notes = models.TextField(blank=True)
    
    # Metadata
    reported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['severity', 'reported_at']
        verbose_name_plural = 'Emergency cases'
        
    def __str__(self):
        return f"Emergency: {self.pet.name} - {self.get_severity_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-assign queue number
        if not self.queue_number:
            last_case = EmergencyCase.objects.filter(
                status__in=['WAITING', 'IN_TREATMENT']
            ).order_by('-queue_number').first()
            
            self.queue_number = (last_case.queue_number + 1) if last_case else 1
        
        super().save(*args, **kwargs)


class AppointmentFeedback(models.Model):
    """Patient feedback after appointments"""
    
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    comments = models.TextField(blank=True)
    
    # Specific ratings
    vet_professionalism = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    facility_cleanliness = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    wait_time_satisfaction = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    
    would_recommend = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Feedback for {self.appointment} - {self.rating} stars"
