from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class Pet(models.Model):
    """Pet information model"""
    
    PET_SPECIES = (
        ('DOG', 'Dog'),
        ('CAT', 'Cat'),
        ('BIRD', 'Bird'),
        ('RABBIT', 'Rabbit'),
        ('OTHER', 'Other'),
    )
    
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=20, choices=PET_SPECIES)
    breed = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    color = models.CharField(max_length=50)
    weight = models.DecimalField(max_digits=6, decimal_places=2, help_text="Weight in kg")
    microchip_id = models.CharField(max_length=50, blank=True, unique=True, null=True)
    photo = models.ImageField(upload_to='pets/', null=True, blank=True)
    
    # Medical info
    allergies = models.TextField(blank=True, help_text="Known allergies")
    medical_conditions = models.TextField(blank=True, help_text="Chronic conditions")
    special_notes = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} ({self.get_species_display()}) - {self.owner.get_full_name()}"
    
    @property
    def age(self):
        """Calculate pet's age"""
        today = timezone.now().date()
        age = today.year - self.date_of_birth.year
        if today.month < self.date_of_birth.month or \
           (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1
        return age


class MedicalRecord(models.Model):
    """Medical history and visit records"""
    
    VISIT_TYPE = (
        ('CHECKUP', 'Regular Checkup'),
        ('EMERGENCY', 'Emergency'),
        ('FOLLOWUP', 'Follow-up'),
        ('VACCINATION', 'Vaccination'),
        ('SURGERY', 'Surgery'),
        ('DIAGNOSIS', 'Diagnosis'),
    )
    
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='medical_records')
    veterinarian = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='medical_records_created'
    )
    visit_date = models.DateTimeField(default=timezone.now)
    visit_type = models.CharField(max_length=20, choices=VISIT_TYPE)
    
    # Visit details
    symptoms = models.TextField()
    diagnosis = models.TextField()
    treatment = models.TextField()
    notes = models.TextField(blank=True)
    
    # Vital signs
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="°F")
    heart_rate = models.IntegerField(null=True, blank=True, help_text="BPM")
    respiratory_rate = models.IntegerField(null=True, blank=True, help_text="per minute")
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="kg")
    
    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-visit_date']
        
    def __str__(self):
        return f"{self.pet.name} - {self.get_visit_type_display()} on {self.visit_date.date()}"


class Prescription(models.Model):
    """Prescription details"""
    
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='prescriptions')
    medication_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100, help_text="e.g., Twice daily")
    duration = models.CharField(max_length=100, help_text="e.g., 7 days")
    instructions = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.medication_name} - {self.medical_record.pet.name}"


class Vaccination(models.Model):
    """Vaccination records and schedules"""
    
    VACCINE_STATUS = (
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    )
    
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='vaccinations')
    vaccine_name = models.CharField(max_length=200)
    disease_protection = models.CharField(max_length=200, help_text="Disease(s) it protects against")
    
    scheduled_date = models.DateField()
    administered_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=VACCINE_STATUS, default='SCHEDULED')
    
    veterinarian = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vaccinations_administered'
    )
    
    batch_number = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
        
    def __str__(self):
        return f"{self.vaccine_name} for {self.pet.name} - {self.status}"
    
    def save(self, *args, **kwargs):
        """Automatically update status based on dates"""
        today = timezone.now().date()
        
        if self.administered_date:
            self.status = 'COMPLETED'
        elif self.scheduled_date < today and not self.administered_date:
            self.status = 'OVERDUE'
        
        super().save(*args, **kwargs)


class MedicalDocument(models.Model):
    """Medical documents (X-rays, lab reports, etc.)"""
    
    DOCUMENT_TYPES = (
        ('XRAY', 'X-Ray'),
        ('LAB', 'Lab Report'),
        ('SCAN', 'Scan'),
        ('REPORT', 'Medical Report'),
        ('OTHER', 'Other'),
    )
    
    medical_record = models.ForeignKey(
        MedicalRecord, 
        on_delete=models.CASCADE, 
        related_name='documents',
        null=True,
        blank=True
    )
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='documents')
    
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='medical_documents/')
    
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return f"{self.title} - {self.pet.name}"
