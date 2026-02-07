from django.contrib import admin
from .models import SkinDiseaseImage, DiagnosisResult, TreatmentRecommendation, AIModelMetrics


@admin.register(SkinDiseaseImage)
class SkinDiseaseImageAdmin(admin.ModelAdmin):
    list_display = ['pet', 'uploaded_by', 'status', 'uploaded_at']
    list_filter = ['status', 'uploaded_at']
    search_fields = ['pet__name', 'uploaded_by__username']
    readonly_fields = ['image_width', 'image_height', 'file_size', 'uploaded_at']
    date_hierarchy = 'uploaded_at'


@admin.register(DiagnosisResult)
class DiagnosisResultAdmin(admin.ModelAdmin):
    list_display = ['skin_disease_image', 'predicted_disease', 'confidence_level', 'urgency_level', 'vet_confirmed']
    list_filter = ['predicted_disease', 'confidence_level', 'urgency_level', 'vet_confirmed']
    search_fields = ['skin_disease_image__pet__name']
    readonly_fields = ['created_at', 'updated_at', 'confidence_level']


@admin.register(TreatmentRecommendation)
class TreatmentRecommendationAdmin(admin.ModelAdmin):
    list_display = ['disease', 'contagious', 'recovery_time']
    list_filter = ['contagious']
    search_fields = ['disease', 'description']


@admin.register(AIModelMetrics)
class AIModelMetricsAdmin(admin.ModelAdmin):
    list_display = ['model_version', 'date', 'accuracy_rate', 'total_predictions', 'average_confidence']
    list_filter = ['model_version', 'date']
    readonly_fields = ['date']
