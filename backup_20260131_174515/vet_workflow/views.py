from django.shortcuts import render
from appointments.models import EmergencyCase

def home(request):
    """Home page view with role-specific context data"""
    context = {}
    
    if request.user.is_authenticated and request.user.role == 'VET':
        # Add active emergencies specifically assigned to this doctor
        context['active_emergencies'] = EmergencyCase.objects.filter(
            assigned_vet=request.user,
            status__in=['WAITING', 'IN_TREATMENT']
        )
        
    return render(request, 'home.html', context)


def services(request):
    """Services page view"""
    return render(request, 'services.html')


def about(request):
    """About Us page view"""
    return render(request, 'about.html')
