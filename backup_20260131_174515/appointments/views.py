from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Appointment, EmergencyCase, DoctorAvailability
from medical_records.models import Pet
from accounts.models import User
from datetime import datetime, date

@login_required
def appointment_list(request):
    """List all appointments"""
    if request.user.is_pet_owner:
        appointments = Appointment.objects.filter(owner=request.user).order_by('appointment_date', 'appointment_time')
    elif request.user.is_veterinarian:
        appointments = Appointment.objects.filter(
            veterinarian=request.user,
            status__in=['SCHEDULED', 'CONFIRMED', 'IN_PROGRESS']
        ).order_by('appointment_date', 'appointment_time')
    else:
        appointments = Appointment.objects.all().order_by('appointment_date', 'appointment_time')
    
    return render(request, 'appointments/list.html', {'appointments': appointments})

@login_required
def book_appointment(request):
    """Book a new appointment"""
    if request.method == 'POST':
        try:
            pet_id = request.POST.get('pet')
            vet_id = request.POST.get('veterinarian')
            appointment_date_str = request.POST.get('appointment_date')
            appointment_time_str = request.POST.get('appointment_time')
            
            # Convert strings to objects
            appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
            
            # CHECK DOCTOR AVAILABILITY
            if vet_id:
                # 1. Check for specific date override
                avail = DoctorAvailability.objects.filter(
                    veterinarian_id=vet_id,
                    date=appointment_date
                ).first()
                
                # 2. If no specific date, check recurring day of week
                if not avail:
                    avail = DoctorAvailability.objects.filter(
                        veterinarian_id=vet_id,
                        day_of_week=appointment_date.weekday(),
                        date__isnull=True
                    ).first()
                
                if avail:
                    if not avail.is_available:
                        messages.error(request, 'The doctor is not available on this date.')
                        return redirect('appointments:book')
                    
                    if appointment_time < avail.start_time or appointment_time > avail.end_time:
                        messages.error(request, f'The doctor is only available between {avail.start_time} and {avail.end_time}.')
                        return redirect('appointments:book')
                # If no availability record is found, we allow the booking by default
                # This prevents blocking all dates if the doctor hasn't set a schedule yet.

            appointment = Appointment.objects.create(
                pet_id=pet_id,
                owner=request.user,
                veterinarian_id=vet_id if vet_id else None,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                duration=int(request.POST.get('duration', 30)),
                reason=request.POST.get('reason'),
                is_emergency=request.POST.get('is_emergency') == 'on',
                created_by=request.user
            )

            # Create an EmergencyCase record if it's an emergency
            if appointment.is_emergency:
                EmergencyCase.objects.create(
                    appointment=appointment,
                    pet=appointment.pet,
                    owner=appointment.owner,
                    severity='MODERATE',  # Default severity
                    symptoms=appointment.reason,
                    situation_description=appointment.reason,
                    assigned_vet=appointment.veterinarian
                )
            
            messages.success(request, f'Appointment booked successfully for {appointment.appointment_date}!')
            return redirect('appointments:list')
        except Exception as e:
            messages.error(request, f'Error booking appointment: {str(e)}')
    
    # Get user's pets
    pets = Pet.objects.filter(owner=request.user) if request.user.is_pet_owner else Pet.objects.all()
    
    # Get available veterinarians
    veterinarians = User.objects.filter(role='VET', is_active=True)
    
    # Pass today's date for the form
    today = date.today()
    
    # Get explicitly unavailable dates for veterinarians
    unavailable_dates = DoctorAvailability.objects.filter(
        is_available=False,
        date__gte=today
    ).select_related('veterinarian').values('date', 'veterinarian__first_name', 'veterinarian__last_name')

    # Get recurring unavailable days
    unavailable_days = DoctorAvailability.objects.filter(
        is_available=False,
        date__isnull=True
    ).select_related('veterinarian')
    
    return render(request, 'appointments/book.html', {
        'pets': pets,
        'veterinarians': veterinarians,
        'today': today,
        'unavailable_dates': unavailable_dates,
        'unavailable_days': unavailable_days
    })

@login_required
def finish_appointment(request, pk):
    """Mark an appointment as completed and resolve linked emergency if exists"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check permission (only the assigned vet or staff)
    if request.user == appointment.veterinarian or request.user.is_staff:
        appointment.status = 'COMPLETED'
        appointment.save()
        
        # If this is an emergency, resolve the case too
        if hasattr(appointment, 'emergency_case'):
            emergency = appointment.emergency_case
            emergency.status = 'RESOLVED'
            emergency.treatment_completed_at = timezone.now()
            emergency.save()
            
        messages.success(request, f'Appointment for {appointment.pet.name} marked as finished.')
    else:
        messages.error(request, 'You do not have permission to finish this appointment.')
    
    return redirect('appointments:list')

@login_required
def resolve_emergency(request, pk):
    """Mark an emergency case as resolved directly"""
    case = get_object_or_404(EmergencyCase, pk=pk)
    
    if request.user == case.assigned_vet or request.user.is_staff:
        case.status = 'RESOLVED'
        case.treatment_completed_at = timezone.now()
        case.save()
        
        # Also finish the linked appointment if it exists
        if case.appointment:
            case.appointment.status = 'COMPLETED'
            case.appointment.save()
            
        messages.success(request, f'Emergency case for {case.pet.name} resolved.')
    else:
        messages.error(request, 'You do not have permission to resolve this case.')
    
    return redirect('appointments:emergency')

@login_required
def appointment_detail(request, pk):
    """View appointment details"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check permission
    if not request.user.is_staff and appointment.owner != request.user and appointment.veterinarian != request.user:
        messages.error(request, 'You do not have permission to view this appointment.')
        return redirect('appointments:list')
    
    return render(request, 'appointments/detail.html', {'appointment': appointment})

@login_required
def cancel_appointment(request, pk):
    """Cancel an appointment"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check permission
    if request.user == appointment.owner or request.user.is_staff:
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
    else:
        messages.error(request, 'You do not have permission to cancel this appointment.')
    
    return redirect('appointments:list')

@login_required
def doctor_availability(request):
    """View doctor availability"""
    if request.user.is_veterinarian:
        availabilities = DoctorAvailability.objects.filter(veterinarian=request.user)
    else:
        availabilities = DoctorAvailability.objects.all()
    
    return render(request, 'appointments/availability.html', {'availabilities': availabilities})

@login_required
def manage_availability(request):
    """Add or update doctor availability"""
    if not request.user.is_veterinarian:
        messages.error(request, 'Only veterinarians can manage their availability.')
        return redirect('appointments:list')
        
    if request.method == 'POST':
        day_of_week = request.POST.get('day_of_week')
        date_val = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        is_available = request.POST.get('is_available') == 'on'
        
        if not day_of_week and not date_val:
            messages.error(request, 'Please select either a day of the week or a specific date.')
            return render(request, 'appointments/manage_availability.html')

        # If not available, times can be null or a dummy value
        if not is_available:
            if not start_time: start_time = "09:00"
            if not end_time: end_time = "17:00"
        elif not start_time or not end_time:
            messages.error(request, 'Start and end times are required when marking as available.')
            return render(request, 'appointments/manage_availability.html')

        try:
            # Prepare search criteria
            criteria = {'veterinarian': request.user}
            if date_val:
                criteria['date'] = date_val
            else:
                criteria['day_of_week'] = day_of_week
                criteria['date'] = None # Ensure we don't match a date-specific entry

            # Update or create
            availability, created = DoctorAvailability.objects.update_or_create(
                **criteria,
                defaults={
                    'start_time': start_time,
                    'end_time': end_time,
                    'is_available': is_available,
                    'day_of_week': day_of_week if not date_val else None
                }
            )
            
            label = availability.date if availability.date else availability.get_day_of_week_display()
            messages.success(request, f'Availability for {label} updated successfully!')
            return redirect('appointments:availability')
        except Exception as e:
            messages.error(request, f'Error saving availability: {str(e)}')
            
    return render(request, 'appointments/manage_availability.html')

from django.http import JsonResponse

@login_required
def get_doctor_schedule(request):
    """AJAX view to get all availability rules for a doctor"""
    vet_id = request.GET.get('vet_id')
    if not vet_id:
        return JsonResponse({'error': 'Missing vet_id'}, status=400)
    
    availabilities = DoctorAvailability.objects.filter(veterinarian_id=vet_id)
    
    schedule = {
        'recurring': {}, # day_of_week -> details
        'specific': {}   # date_str -> details
    }
    
    for avail in availabilities:
        data = {
            'is_available': avail.is_available,
            'start_time': avail.start_time.strftime('%H:%M'),
            'end_time': avail.end_time.strftime('%H:%M'),
        }
        if avail.date:
            schedule['specific'][avail.date.strftime('%Y-%m-%d')] = data
        else:
            schedule['recurring'][avail.day_of_week] = data
            
    return JsonResponse(schedule)

@login_required
def check_availability(request):
    """AJAX view to check doctor availability for a specific date and time"""
    vet_id = request.GET.get('vet_id')
    date_str = request.GET.get('date')
    time_str = request.GET.get('time')
    
    if not vet_id or not date_str:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        check_time = datetime.strptime(time_str, '%H:%M').time() if time_str else None
        
        # 1. Check for specific date override
        avail = DoctorAvailability.objects.filter(
            veterinarian_id=vet_id,
            date=check_date
        ).first()
        
        # 2. If no specific date, check recurring day of week
        if not avail:
            avail = DoctorAvailability.objects.filter(
                veterinarian_id=vet_id,
                day_of_week=check_date.weekday(),
                date__isnull=True
            ).first()
            
        if avail:
            is_available = avail.is_available
            reason = ""
            
            if is_available and check_time:
                if check_time < avail.start_time or check_time > avail.end_time:
                    is_available = False
                    reason = f"Outside working hours ({avail.start_time.strftime('%H:%M')} - {avail.end_time.strftime('%H:%M')})"
            
            return JsonResponse({
                'is_available': is_available,
                'start_time': avail.start_time.strftime('%H:%M'),
                'end_time': avail.end_time.strftime('%H:%M'),
                'has_schedule': True,
                'reason': reason
            })
        else:
            return JsonResponse({
                'is_available': True,
                'has_schedule': False,
                'message': 'No specific schedule set - bookings allowed.'
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_availability(request, pk):
    """Delete an availability record"""
    availability = get_object_or_404(DoctorAvailability, pk=pk)
    
    # Check permission (only the veterinarian who owns it or staff)
    if request.user == availability.veterinarian or request.user.is_staff:
        availability.delete()
        messages.success(request, 'Availability record deleted successfully.')
    else:
        messages.error(request, 'You do not have permission to delete this record.')
    
    return redirect('appointments:availability')

@login_required
def emergency_cases(request):
    """View emergency cases assigned to the current vet"""
    if request.user.is_staff:
        # Admins see everything
        cases = EmergencyCase.objects.filter(status__in=['WAITING', 'IN_TREATMENT']).order_by('severity', 'reported_at')
    elif request.user.role == 'VET':
        # Veterinarians only see their own assigned cases
        cases = EmergencyCase.objects.filter(
            assigned_vet=request.user,
            status__in=['WAITING', 'IN_TREATMENT']
        ).order_by('severity', 'reported_at')
    else:
        cases = EmergencyCase.objects.none()
    
    return render(request, 'appointments/emergency.html', {'cases': cases})
