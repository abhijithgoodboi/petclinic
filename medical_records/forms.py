from django import forms
from .models import MedicalRecord, Pet

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = [
            'visit_type', 'symptoms', 'diagnosis', 'treatment', 'notes',
            'temperature', 'heart_rate', 'respiratory_rate', 'weight',
            'follow_up_required', 'follow_up_date'
        ]
        widgets = {
            'visit_type': forms.Select(attrs={'class': 'form-select'}),
            'symptoms': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'treatment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'heart_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'respiratory_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'follow_up_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'follow_up_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
