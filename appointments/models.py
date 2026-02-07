from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from medical_records.models import Pet
from datetime import datetime, timedelta


class ClinicSettings(models.Model):
    """Clinic-wide settings for working hours and off days"""
    
    DAYS_OF_WEEK = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    name = models.CharField(max_length=200, default="Ernakulam Pet Hospital")
    
    # Working hours
    opening_time = models.TimeField(default="09:00")
    closing_time = models.TimeField(default="18:00")
    
    # Off days (comma-separated day numbers: 0=Monday, 6=Sunday)
    weekly_off_days = models.CharField(
        max_length=20, 
        default="6",  # Sunday off by default
        help_text="Comma-separated day numbers (0=Monday, 6=Sunday)"
    )
    
    # Slot duration in minutes
    slot_duration = models.IntegerField(default=30, help_text="Appointment slot duration in minutes")
    
    # Emergency settings
    emergency_enabled = models.BooleanField(default=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    
    # Average wait time per patient (for queue estimation)
    avg_consultation_time = models.IntegerField(default=15, help_text="Average consultation time in minutes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Clinic Settings"
        verbose_name_plural = "Clinic Settings"
    
    def __str__(self):
        return self.name
    
    @property
    def off_days_list(self):
        """Return list of off day integers"""
        if self.weekly_off_days:
            return [int(d.strip()) for d in self.weekly_off_days.split(',') if d.strip()]
        return []
    
    def is_clinic_open(self, check_date=None):
        """Check if clinic is open on a given date"""
        if check_date is None:
            check_date = timezone.now().date()
        
        # Check if it's a weekly off day
        if check_date.weekday() in self.off_days_list:
            return False
        
        # Check for specific holiday
        if ClinicHoliday.objects.filter(date=check_date).exists():
            return False
        
        return True


class ClinicHoliday(models.Model):
    """Specific dates when the clinic is closed"""
    
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=200)
    is_recurring = models.BooleanField(default=False, help_text="Repeats every year")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date']
    
    def __str__(self):
        return f"{self.date} - {self.reason}"


class DoctorStatus(models.Model):
    """Track real-time doctor status (available, busy, on leave)"""
    
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('BUSY', 'Busy with Patient'),
        ('ON_LEAVE', 'On Leave'),
        ('BREAK', 'On Break'),
        ('EMERGENCY', 'Handling Emergency'),
        ('OFF_DUTY', 'Off Duty'),
    )
    
    veterinarian = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='current_status',
        limit_choices_to={'role': 'VET'}
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    status_message = models.CharField(max_length=200, blank=True, help_text="Custom status message")
    
    # Leave tracking
    leave_start = models.DateField(null=True, blank=True)
    leave_end = models.DateField(null=True, blank=True)
    leave_reason = models.CharField(max_length=200, blank=True)
    
    # Current patient (if busy)
    current_appointment = models.ForeignKey(
        'Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_doctor_status'
    )
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Doctor Statuses"
    
    def __str__(self):
        return f"Dr. {self.veterinarian.get_full_name()} - {self.get_status_display()}"
    
    def is_on_leave_today(self):
        """Check if doctor is on leave today"""
        today = timezone.now().date()
        if self.leave_start and self.leave_end:
            return self.leave_start <= today <= self.leave_end
        return self.status == 'ON_LEAVE'
    
    def is_available_for_booking(self):
        """Check if doctor can accept new bookings"""
        if self.is_on_leave_today():
            return False
        return self.status in ['AVAILABLE', 'BUSY', 'BREAK']


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
    
    # Token/Queue System
    token_number = models.IntegerField(null=True, blank=True, help_text="Daily token number")
    check_in_time = models.DateTimeField(null=True, blank=True, help_text="When patient checked in")
    queue_position = models.IntegerField(null=True, blank=True, help_text="Current position in queue")
    
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


class GroomingService(models.Model):
    """Available grooming services"""
    
    SERVICE_TYPES = (
        ('BATHING', 'Bathing'),
        ('HAIR_TRIMMING', 'Hair Trimming'),
        ('NAIL_CLIPPING', 'Nail Clipping'),
        ('FULL_GROOMING', 'Full Grooming Package'),
        ('EAR_CLEANING', 'Ear Cleaning'),
        ('TEETH_CLEANING', 'Teeth Cleaning'),
        ('DESHEDDING', 'De-shedding Treatment'),
    )
    
    name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    description = models.TextField(blank=True)
    duration = models.IntegerField(default=30, help_text="Duration in minutes")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Pet size pricing variations
    small_pet_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    medium_pet_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    large_pet_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - Rs.{self.price}"


class GroomingAppointment(models.Model):
    """Grooming appointment bookings (separate from medical appointments)"""
    
    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('CONFIRMED', 'Confirmed'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    )
    
    PET_SIZE = (
        ('SMALL', 'Small (< 10 kg)'),
        ('MEDIUM', 'Medium (10-25 kg)'),
        ('LARGE', 'Large (> 25 kg)'),
    )
    
    # Basic info
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='grooming_appointments')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='grooming_appointments_as_owner'
    )
    
    # Services selected
    services = models.ManyToManyField(GroomingService, related_name='appointments')
    pet_size = models.CharField(max_length=10, choices=PET_SIZE, default='MEDIUM')
    
    # Appointment details
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    
    # Token/Queue
    token_number = models.IntegerField(null=True, blank=True)
    
    # Pricing
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Notes
    special_instructions = models.TextField(blank=True, help_text="Special grooming instructions")
    notes = models.TextField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='grooming_appointments_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
    
    def __str__(self):
        return f"Grooming: {self.pet.name} - {self.appointment_date} at {self.appointment_time}"
    
    def calculate_total_duration(self):
        """Calculate total duration of all services"""
        return sum(s.duration for s in self.services.all())
    
    def calculate_total_price(self):
        """Calculate total price based on pet size"""
        total = 0
        for service in self.services.all():
            if self.pet_size == 'SMALL' and service.small_pet_price:
                total += service.small_pet_price
            elif self.pet_size == 'LARGE' and service.large_pet_price:
                total += service.large_pet_price
            elif self.pet_size == 'MEDIUM' and service.medium_pet_price:
                total += service.medium_pet_price
            else:
                total += service.price
        return total
    
    def save(self, *args, **kwargs):
        # Calculate end time based on services
        if not self.end_time and self.appointment_time and self.pk:
            duration = self.calculate_total_duration()
            start = datetime.combine(self.appointment_date, self.appointment_time)
            end = start + timedelta(minutes=duration)
            self.end_time = end.time()
        
        # Calculate total price
        if self.pk:
            self.total_price = self.calculate_total_price()
        
        super().save(*args, **kwargs)


class QueueStatus(models.Model):
    """Real-time queue status for today's appointments"""
    
    date = models.DateField(unique=True)
    current_token = models.IntegerField(default=0)
    last_called_token = models.IntegerField(default=0)
    
    # Statistics
    total_appointments = models.IntegerField(default=0)
    completed_appointments = models.IntegerField(default=0)
    avg_wait_time = models.IntegerField(default=0, help_text="Average wait time in minutes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Queue Statuses"
    
    def __str__(self):
        return f"Queue Status for {self.date} - Token #{self.current_token}"
    
    @classmethod
    def get_today_status(cls):
        """Get or create today's queue status"""
        today = timezone.now().date()
        status, created = cls.objects.get_or_create(date=today)
        return status
    
    def get_next_token(self):
        """Generate next token number"""
        self.current_token += 1
        self.save()
        return self.current_token
    
    def get_estimated_wait_time(self, token_number):
        """Estimate wait time based on position in queue"""
        if token_number <= self.last_called_token:
            return 0
        
        positions_ahead = token_number - self.last_called_token
        # Use average wait time or default 15 minutes per patient
        avg_time = self.avg_wait_time if self.avg_wait_time > 0 else 15
        return positions_ahead * avg_time
