from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, date
import json

from .models import Pet, MedicalRecord, Vaccination, Prescription
from .forms import MedicalRecordForm

@login_required
def add_medical_record(request, pet_pk):
    """Add a new medical record for a pet with optional prescriptions"""
    pet = get_object_or_404(Pet, pk=pet_pk)
    
    if not (request.user.role == 'VET' or request.user.is_staff):
        messages.error(request, 'Only veterinarians can add medical records.')
        return redirect('medical_records:pet_detail', pk=pet_pk)
        
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.pet = pet
            record.veterinarian = request.user
            record.save()
            
            # Handle prescriptions (submitted as JSON)
            prescriptions_data = request.POST.get('prescriptions_json')
            if prescriptions_data:
                try:
                    prescriptions_list = json.loads(prescriptions_data)
                    for item in prescriptions_list:
                        Prescription.objects.create(
                            medical_record=record,
                            medication_name=item.get('name'),
                            dosage=item.get('dosage'),
                            frequency=item.get('frequency'),
                            duration=item.get('duration'),
                            instructions=item.get('instructions', '')
                        )
                except Exception as e:
                    messages.warning(request, f'Medical record saved, but there was an error saving some prescriptions: {str(e)}')
            
            messages.success(request, f'Medical record for {pet.name} saved successfully.')
            return redirect('medical_records:pet_detail', pk=pet_pk)
    else:
        # Pre-fill weight from pet profile
        form = MedicalRecordForm(initial={'weight': pet.weight})
        
    return render(request, 'medical_records/add_record.html', {
        'form': form,
        'pet': pet
    })

@login_required
def pet_list(request):
    """List all pets for the current user"""
    if request.user.is_pet_owner or request.user.is_staff:
        pets = Pet.objects.filter(owner=request.user) if not request.user.is_staff else Pet.objects.all()
    else:
        # Veterinarians see all pets
        pets = Pet.objects.all()
    
    return render(request, 'medical_records/pet_list.html', {'pets': pets})

@login_required
def add_pet(request):
    """Add a new pet"""
    if request.method == 'POST':
        try:
            pet = Pet.objects.create(
                owner=request.user,
                name=request.POST.get('name'),
                species=request.POST.get('species'),
                breed=request.POST.get('breed'),
                gender=request.POST.get('gender'),
                date_of_birth=request.POST.get('date_of_birth'),
                color=request.POST.get('color'),
                weight=request.POST.get('weight'),
                microchip_id=request.POST.get('microchip_id') or None,
                allergies=request.POST.get('allergies', ''),
                medical_conditions=request.POST.get('medical_conditions', ''),
                special_notes=request.POST.get('special_notes', ''),
            )
            
            # Handle photo upload if present
            if 'photo' in request.FILES:
                pet.photo = request.FILES['photo']
                pet.save()
            
            messages.success(request, f'Pet {pet.name} added successfully!')
            return redirect('medical_records:pet_list')
        except Exception as e:
            messages.error(request, f'Error adding pet: {str(e)}')
    
    return render(request, 'medical_records/add_pet.html')

@login_required
def pet_detail(request, pk):
    """View pet details"""
    pet = get_object_or_404(Pet, pk=pk)
    
    # Check permission: Staff, Veterinarians, and the Pet Owner can view
    if not (request.user.is_staff or request.user.role == 'VET' or pet.owner == request.user):
        messages.error(request, 'You do not have permission to view this pet.')
        return redirect('medical_records:pet_list')
    
    medical_records = pet.medical_records.all()[:5]
    vaccinations = pet.vaccinations.all()[:5]
    
    return render(request, 'medical_records/pet_detail.html', {
        'pet': pet,
        'medical_records': medical_records,
        'vaccinations': vaccinations
    })

@login_required
def medical_record_detail(request, pk):
    """View medical record details"""
    record = get_object_or_404(MedicalRecord, pk=pk)
    
    # Check permission
    if not (request.user.is_staff or request.user.role == 'VET' or record.pet.owner == request.user):
        messages.error(request, 'You do not have permission to view this medical record.')
        return redirect('medical_records:pet_list')
        
    return render(request, 'medical_records/record_detail.html', {'record': record})

@login_required
def vaccination_list(request):
    """List all vaccinations"""
    if request.user.role == 'VET' or request.user.is_staff:
        vaccinations = Vaccination.objects.all().order_by('scheduled_date')
    else:
        vaccinations = Vaccination.objects.filter(pet__owner=request.user).order_by('scheduled_date')
    
    return render(request, 'medical_records/vaccination_list.html', {'vaccinations': vaccinations})

@login_required
def add_vaccination(request, pet_pk):
    """Add a new vaccination schedule for a pet"""
    pet = get_object_or_404(Pet, pk=pet_pk)
    
    if not (request.user.role == 'VET' or request.user.is_staff):
        messages.error(request, 'Only veterinarians can schedule vaccinations.')
        return redirect('medical_records:pet_detail', pk=pet_pk)
        
    if request.method == 'POST':
        try:
            scheduled_date_str = request.POST.get('scheduled_date')
            scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
            
            Vaccination.objects.create(
                pet=pet,
                vaccine_name=request.POST.get('vaccine_name'),
                disease_protection=request.POST.get('disease_protection'),
                scheduled_date=scheduled_date,
                batch_number=request.POST.get('batch_number', ''),
                manufacturer=request.POST.get('manufacturer', ''),
                notes=request.POST.get('notes', '')
            )
            messages.success(request, f'Vaccination scheduled for {pet.name}.')
            return redirect('medical_records:pet_detail', pk=pet_pk)
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            
    return render(request, 'medical_records/add_vaccination.html', {'pet': pet})

@login_required
def administer_vaccination(request, pk):
    """Mark a vaccination as administered/completed"""
    vaccination = get_object_or_404(Vaccination, pk=pk)
    
    if not (request.user.role == 'VET' or request.user.is_staff):
        messages.error(request, 'Only veterinarians can administer vaccinations.')
        return redirect('medical_records:pet_detail', pk=vaccination.pet.pk)
        
    vaccination.administered_date = timezone.now().date()
    vaccination.veterinarian = request.user
    vaccination.status = 'COMPLETED'
    vaccination.save()
    
    messages.success(request, f'Vaccination {vaccination.vaccine_name} administered successfully.')
    return redirect('medical_records:pet_detail', pk=vaccination.pet.pk)


# ============== VACCINATION DASHBOARD ==============

@login_required
def vaccination_dashboard(request, pet_pk=None):
    """Comprehensive vaccination dashboard for a pet"""
    
    if pet_pk:
        pet = get_object_or_404(Pet, pk=pet_pk)
        # Permission check
        if not (request.user.is_staff or request.user.role == 'VET' or pet.owner == request.user):
            messages.error(request, 'Permission denied.')
            return redirect('medical_records:pet_list')
        
        vaccinations = Vaccination.objects.filter(pet=pet)
    else:
        pet = None
        if request.user.is_pet_owner:
            vaccinations = Vaccination.objects.filter(pet__owner=request.user)
        else:
            vaccinations = Vaccination.objects.all()
    
    today = timezone.now().date()
    
    # Categorize vaccinations
    completed = vaccinations.filter(status='COMPLETED').order_by('-administered_date')
    upcoming = vaccinations.filter(status='SCHEDULED', scheduled_date__gte=today).order_by('scheduled_date')
    overdue = vaccinations.filter(status='OVERDUE').order_by('scheduled_date')
    
    # Also check for scheduled vaccines that are now overdue
    for v in vaccinations.filter(status='SCHEDULED', scheduled_date__lt=today):
        v.status = 'OVERDUE'
        v.save()
        overdue = vaccinations.filter(status='OVERDUE').order_by('scheduled_date')
    
    # Get pets for dropdown (if no specific pet selected)
    if request.user.is_pet_owner:
        pets = Pet.objects.filter(owner=request.user)
    else:
        pets = Pet.objects.all()
    
    return render(request, 'medical_records/vaccination_dashboard.html', {
        'pet': pet,
        'pets': pets,
        'completed': completed,
        'upcoming': upcoming,
        'overdue': overdue,
        'total_completed': completed.count(),
        'total_upcoming': upcoming.count(),
        'total_overdue': overdue.count(),
    })


# ============== MEDICAL HISTORY FOR OWNERS ==============

@login_required
def medical_history(request, pet_pk=None):
    """View complete medical history for a pet (owner-friendly view)"""
    
    if pet_pk:
        pet = get_object_or_404(Pet, pk=pet_pk)
        # Permission check
        if not (request.user.is_staff or request.user.role == 'VET' or pet.owner == request.user):
            messages.error(request, 'Permission denied.')
            return redirect('medical_records:pet_list')
        
        records = MedicalRecord.objects.filter(pet=pet).order_by('-visit_date')
        vaccinations = Vaccination.objects.filter(pet=pet).order_by('-scheduled_date')
    else:
        pet = None
        if request.user.is_pet_owner:
            records = MedicalRecord.objects.filter(pet__owner=request.user).order_by('-visit_date')
            vaccinations = Vaccination.objects.filter(pet__owner=request.user).order_by('-scheduled_date')
        else:
            records = MedicalRecord.objects.all().order_by('-visit_date')
            vaccinations = Vaccination.objects.all().order_by('-scheduled_date')
    
    # Get pets for dropdown
    if request.user.is_pet_owner:
        pets = Pet.objects.filter(owner=request.user)
    else:
        pets = Pet.objects.all()
    
    # Group records by year-month for timeline
    records_by_month = {}
    for record in records:
        month_key = record.visit_date.strftime('%B %Y')
        if month_key not in records_by_month:
            records_by_month[month_key] = []
        records_by_month[month_key].append(record)
    
    return render(request, 'medical_records/medical_history.html', {
        'pet': pet,
        'pets': pets,
        'records': records,
        'vaccinations': vaccinations,
        'records_by_month': records_by_month,
        'total_records': records.count(),
        'total_vaccinations': vaccinations.count(),
    })