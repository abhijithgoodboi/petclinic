from django.contrib import admin
from .models import Pet, MedicalRecord, Prescription, Vaccination, MedicalDocument


class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 1


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ['name', 'species', 'breed', 'owner', 'age', 'is_active']
    list_filter = ['species', 'gender', 'is_active']
    search_fields = ['name', 'owner__username', 'microchip_id']
    readonly_fields = ['age', 'created_at', 'updated_at']


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['pet', 'veterinarian', 'visit_date', 'visit_type', 'follow_up_required']
    list_filter = ['visit_type', 'follow_up_required', 'visit_date']
    search_fields = ['pet__name', 'veterinarian__username', 'diagnosis']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PrescriptionInline]
    date_hierarchy = 'visit_date'


@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ['pet', 'vaccine_name', 'scheduled_date', 'status', 'veterinarian']
    list_filter = ['status', 'scheduled_date']
    search_fields = ['pet__name', 'vaccine_name']
    date_hierarchy = 'scheduled_date'


@admin.register(MedicalDocument)
class MedicalDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'pet', 'document_type', 'uploaded_by', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['title', 'pet__name']
    date_hierarchy = 'uploaded_at'
