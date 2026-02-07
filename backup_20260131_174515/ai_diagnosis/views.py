from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import SkinDiseaseImage, DiagnosisResult
from .ai_model import analyze_skin_image, get_treatment_info
from medical_records.models import Pet

@login_required
def diagnosis_home(request):
    """AI diagnosis home page"""
    if request.user.role == 'VET' or request.user.is_staff:
        recent_diagnoses = SkinDiseaseImage.objects.all().order_by('-uploaded_at')[:5]
    else:
        recent_diagnoses = SkinDiseaseImage.objects.filter(
            uploaded_by=request.user
        ).order_by('-uploaded_at')[:5]
    
    return render(request, 'ai_diagnosis/home.html', {
        'recent_diagnoses': recent_diagnoses
    })

@login_required
def upload_image(request):
    """Upload image for AI analysis"""
    if request.method == 'POST':
        try:
            pet_id = request.POST.get('pet')
            image = request.FILES.get('image')
            description = request.POST.get('description', '')
            affected_area = request.POST.get('affected_area', '')
            
            if not image:
                messages.error(request, 'Please select an image to upload.')
                return redirect('ai_diagnosis:upload')
            
            # Create image record
            skin_image = SkinDiseaseImage.objects.create(
                pet_id=pet_id,
                uploaded_by=request.user,
                image=image,
                description=description,
                affected_area=affected_area,
                status='PROCESSING'
            )
            
            # Process with AI
            skin_image.processing_started_at = timezone.now()
            skin_image.save()
            
            try:
                # Analyze image
                result = analyze_skin_image(skin_image.image.path)
                
                # Create diagnosis result
                diagnosis = DiagnosisResult.objects.create(
                    skin_disease_image=skin_image,
                    predicted_disease=result['primary_disease'],
                    confidence_score=result['primary_confidence'],
                    model_version=result['model_version'],
                    processing_time_seconds=result['processing_time']
                )
                
                # Add alternatives
                if result['alternatives']:
                    if len(result['alternatives']) > 0:
                        diagnosis.alternative_diagnosis_1 = result['alternatives'][0]['disease']
                        diagnosis.alternative_confidence_1 = result['alternatives'][0]['confidence']
                    if len(result['alternatives']) > 1:
                        diagnosis.alternative_diagnosis_2 = result['alternatives'][1]['disease']
                        diagnosis.alternative_confidence_2 = result['alternatives'][1]['confidence']
                    if len(result['alternatives']) > 2:
                        diagnosis.alternative_diagnosis_3 = result['alternatives'][2]['disease']
                        diagnosis.alternative_confidence_3 = result['alternatives'][2]['confidence']
                
                # Get treatment recommendations
                treatment = get_treatment_info(diagnosis.predicted_disease)
                diagnosis.recommended_actions = treatment.get('medical_treatment', 'Consult with veterinarian')
                
                diagnosis.save()
                
                # Update image status
                skin_image.status = 'COMPLETED'
                skin_image.processing_completed_at = timezone.now()
                skin_image.save()
                
                messages.success(request, 'Image analyzed successfully!')
                return redirect('ai_diagnosis:result', pk=diagnosis.pk)
                
            except Exception as e:
                skin_image.status = 'FAILED'
                skin_image.save()
                messages.error(request, f'Error analyzing image: {str(e)}')
                return redirect('ai_diagnosis:upload')
                
        except Exception as e:
            messages.error(request, f'Error uploading image: {str(e)}')
    
    # Get user's pets
    pets = Pet.objects.filter(owner=request.user)
    
    return render(request, 'ai_diagnosis/upload.html', {'pets': pets})

@login_required
def diagnosis_result(request, pk):
    """View diagnosis result"""
    result = get_object_or_404(DiagnosisResult, pk=pk)
    
    # Check permission: Owner, Vet, or Staff
    if not (result.skin_disease_image.uploaded_by == request.user or request.user.role == 'VET' or request.user.is_staff):
        messages.error(request, 'You do not have permission to view this result.')
        return redirect('ai_diagnosis:home')
    
    # Get treatment info
    treatment = get_treatment_info(result.predicted_disease)
    
    return render(request, 'ai_diagnosis/result.html', {
        'result': result,
        'treatment': treatment
    })

@login_required
def review_diagnosis(request, pk):
    """Veterinarian review of an AI diagnosis"""
    result = get_object_or_404(DiagnosisResult, pk=pk)
    
    if not (request.user.role == 'VET' or request.user.is_staff):
        messages.error(request, 'Only veterinarians can review diagnoses.')
        return redirect('ai_diagnosis:result', pk=pk)
        
    if request.method == 'POST':
        result.vet_confirmed = request.POST.get('vet_confirmed') == 'true'
        result.vet_diagnosis = request.POST.get('vet_diagnosis')
        result.vet_notes = request.POST.get('vet_notes')
        result.reviewed_by_vet = request.user
        result.reviewed_at = timezone.now()
        result.save()
        
        messages.success(request, 'Clinical review saved successfully.')
        return redirect('ai_diagnosis:result', pk=pk)
    
    return redirect('ai_diagnosis:result', pk=pk)

@login_required
def diagnosis_history(request):
    """View diagnosis history"""
    if request.user.role == 'VET' or request.user.is_staff:
        images = SkinDiseaseImage.objects.all().order_by('-uploaded_at')
    else:
        images = SkinDiseaseImage.objects.filter(
            uploaded_by=request.user
        ).order_by('-uploaded_at')
    
    return render(request, 'ai_diagnosis/history.html', {'images': images})