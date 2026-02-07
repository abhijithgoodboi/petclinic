from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from medical_records.models import Pet

class SkinDiseaseImage(models.Model):
    """Store uploaded images for AI analysis"""
    
    IMAGE_STATUS = (
        ('PENDING', 'Pending Analysis'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )
    
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='skin_disease_images')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    image = models.ImageField(
        upload_to='ai_diagnosis/images/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    
    description = models.TextField(blank=True, help_text="Any additional details about the condition")
    affected_area = models.CharField(max_length=200, blank=True, help_text="Body part affected")
    
    status = models.CharField(max_length=20, choices=IMAGE_STATUS, default='PENDING')
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Image metadata
    image_width = models.IntegerField(null=True, blank=True)
    image_height = models.IntegerField(null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True, help_text="File size in bytes")
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return f"Image for {self.pet.name} - {self.uploaded_at.date()}"
    
    def save(self, *args, **kwargs):
        if self.image:
            from PIL import Image
            img = Image.open(self.image)
            self.image_width = img.width
            self.image_height = img.height
            self.file_size = self.image.size
        
        super().save(*args, **kwargs)


class DiagnosisResult(models.Model):
    """AI diagnosis results for skin diseases"""
    
    DISEASE_CATEGORIES = (
        ('RINGWORM', 'Ringworm'),
        ('MANGE', 'Mange (Scabies)'),
        ('DERMATITIS', 'Dermatitis'),
        ('HOT_SPOT', 'Hot Spot'),
        ('ALLERGY', 'Allergic Reaction'),
        ('FUNGAL', 'Fungal Infection'),
        ('BACTERIAL', 'Bacterial Infection'),
        ('FLEA', 'Flea Allergy'),
        ('ECZEMA', 'Eczema'),
        ('HEALTHY', 'Healthy/No Disease Detected'),
    )
    
    CONFIDENCE_LEVELS = (
        ('VERY_LOW', 'Very Low (< 40%)'),
        ('LOW', 'Low (40-60%)'),
        ('MEDIUM', 'Medium (60-80%)'),
        ('HIGH', 'High (80-95%)'),
        ('VERY_HIGH', 'Very High (> 95%)'),
    )
    
    skin_disease_image = models.OneToOneField(
        SkinDiseaseImage,
        on_delete=models.CASCADE,
        related_name='diagnosis_result'
    )
    
    # Primary diagnosis
    predicted_disease = models.CharField(max_length=50, choices=DISEASE_CATEGORIES)
    confidence_score = models.FloatField(help_text="Confidence score between 0 and 1")
    confidence_level = models.CharField(max_length=20, choices=CONFIDENCE_LEVELS)
    
    # Alternative diagnoses (top 3)
    alternative_diagnosis_1 = models.CharField(max_length=50, choices=DISEASE_CATEGORIES, blank=True)
    alternative_confidence_1 = models.FloatField(null=True, blank=True)
    
    alternative_diagnosis_2 = models.CharField(max_length=50, choices=DISEASE_CATEGORIES, blank=True)
    alternative_confidence_2 = models.FloatField(null=True, blank=True)
    
    alternative_diagnosis_3 = models.CharField(max_length=50, choices=DISEASE_CATEGORIES, blank=True)
    alternative_confidence_3 = models.FloatField(null=True, blank=True)
    
    # AI model info
    model_version = models.CharField(max_length=50, default='v1.0')
    processing_time_seconds = models.FloatField(null=True, blank=True)
    
    # Recommendations
    recommended_actions = models.TextField(blank=True)
    urgency_level = models.CharField(
        max_length=20,
        choices=[
            ('ROUTINE', 'Routine Check-up'),
            ('SOON', 'Schedule Soon'),
            ('URGENT', 'Urgent - Book Immediately'),
            ('EMERGENCY', 'Emergency - Seek Immediate Care'),
        ],
        default='ROUTINE'
    )
    
    # Veterinarian review
    reviewed_by_vet = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_diagnoses',
        limit_choices_to={'role': 'VET'}
    )
    vet_confirmed = models.BooleanField(null=True, blank=True)
    vet_diagnosis = models.CharField(max_length=50, choices=DISEASE_CATEGORIES, blank=True)
    vet_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Diagnosis results'
        
    def __str__(self):
        return f"{self.predicted_disease} for {self.skin_disease_image.pet.name} ({self.confidence_score:.2%})"
    
    def save(self, *args, **kwargs):
        # Automatically determine confidence level
        if self.confidence_score >= 0.95:
            self.confidence_level = 'VERY_HIGH'
        elif self.confidence_score >= 0.80:
            self.confidence_level = 'HIGH'
        elif self.confidence_score >= 0.60:
            self.confidence_level = 'MEDIUM'
        elif self.confidence_score >= 0.40:
            self.confidence_level = 'LOW'
        else:
            self.confidence_level = 'VERY_LOW'
        
        # Set urgency level based on disease and confidence
        if self.predicted_disease in ['MANGE', 'HOT_SPOT'] and self.confidence_score > 0.8:
            self.urgency_level = 'URGENT'
        elif self.predicted_disease == 'HEALTHY':
            self.urgency_level = 'ROUTINE'
        elif self.confidence_score > 0.7:
            self.urgency_level = 'SOON'
        
        super().save(*args, **kwargs)


class TreatmentRecommendation(models.Model):
    """Treatment recommendations database"""
    
    disease = models.CharField(max_length=50, choices=DiagnosisResult.DISEASE_CATEGORIES, unique=True)
    
    # Information
    description = models.TextField()
    symptoms = models.TextField()
    causes = models.TextField()
    
    # Treatment
    home_care = models.TextField(help_text="What owners can do at home")
    medical_treatment = models.TextField(help_text="Professional treatment options")
    prevention = models.TextField(help_text="Prevention tips")
    
    # Prognosis
    recovery_time = models.CharField(max_length=200)
    contagious = models.BooleanField(default=False)
    
    # Additional resources
    external_resources = models.TextField(blank=True, help_text="Links to additional information")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['disease']
        
    def __str__(self):
        return f"Treatment for {self.get_disease_display()}"


class AIModelMetrics(models.Model):
    """Track AI model performance metrics"""
    
    model_version = models.CharField(max_length=50)
    date = models.DateField(auto_now_add=True)
    
    # Performance metrics
    total_predictions = models.IntegerField(default=0)
    accurate_predictions = models.IntegerField(default=0)
    accuracy_rate = models.FloatField(default=0.0)
    
    average_confidence = models.FloatField(default=0.0)
    average_processing_time = models.FloatField(default=0.0, help_text="In seconds")
    
    # Per-disease accuracy
    disease_accuracy_data = models.JSONField(default=dict, blank=True)
    
    # System info
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'AI model metrics'
        unique_together = ['model_version', 'date']
        
    def __str__(self):
        return f"Metrics for {self.model_version} on {self.date}"
