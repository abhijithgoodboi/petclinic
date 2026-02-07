from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import User
from appointments.models import Appointment, EmergencyCase
from medical_records.models import Pet, MedicalRecord
from ai_diagnosis.models import SkinDiseaseImage

from django.http import JsonResponse

def validate_email(request):
    """AJAX view to check if email already exists"""
    email = request.GET.get('email', None)
    data = {
        'is_taken': User.objects.filter(email__iexact=email).exists()
    }
    return JsonResponse(data)

def register(request):
    """User registration view - Only Pet Owners can register publicly.
       Veterinarians must be created by admin in the Django admin panel.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        phone_number = request.POST.get('phone_number', '')
        address = request.POST.get('address', '')

        # Validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'accounts/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return render(request, 'accounts/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return render(request, 'accounts/register.html')

        # Create user as PET OWNER (default role)
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                role='OWNER',  # Only pet owners can register publicly
                phone_number=phone_number,
                address=address
            )

            # Handle profile picture
            if 'profile_picture' in request.FILES:
                user.profile_picture = request.FILES['profile_picture']
                user.save()

            messages.success(request, f'Account created successfully! Welcome, {first_name}!')

            # Auto login after registration - specify backend for multiple auth backends
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            return redirect('home')

        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'accounts/register.html')

    return render(request, 'accounts/register.html')

@login_required
def profile(request):
    """User profile view"""
    context = {'user': request.user}
    
    if request.user.role == 'VET':
        context['active_emergencies_count'] = EmergencyCase.objects.filter(
            assigned_vet=request.user,
            status__in=['WAITING', 'IN_TREATMENT']
        ).count()
        
    return render(request, 'accounts/profile.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    """Admin dashboard with global statistics"""
    stats = {
        'total_users': User.objects.count(),
        'total_pets': Pet.objects.count(),
        'total_appointments': Appointment.objects.count(),
        'total_medical_records': MedicalRecord.objects.count(),
        'total_ai_diagnoses': SkinDiseaseImage.objects.count(),
        'recent_appointments': Appointment.objects.all().order_by('-created_at')[:5],
        'recent_pets': Pet.objects.all().order_by('-created_at')[:5],
    }
    return render(request, 'accounts/admin_dashboard.html', stats)

@login_required
def edit_profile(request):
    """Edit user profile view"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.address = request.POST.get('address', user.address)
        
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
            
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/edit_profile.html')

def logout_view(request):
    """Custom logout view that handles both GET and POST"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')
