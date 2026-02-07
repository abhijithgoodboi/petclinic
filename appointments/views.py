from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db import models
from .models import Appointment, EmergencyCase, DoctorAvailability, DoctorStatus, ClinicSettings
from .ai_bridge import analyze_symptoms_with_groq
from medical_records.models import Pet
from accounts.models import User
from datetime import datetime, date
import json

@login_required
def appointment_list(request):
    """List all appointments (excluding emergencies as they are handled separately)"""
    if request.user.is_pet_owner:
        appointments = Appointment.objects.filter(
            owner=request.user,
            is_emergency=False
        ).order_by('appointment_date', 'appointment_time')
    elif request.user.is_veterinarian:
        appointments = Appointment.objects.filter(
            veterinarian=request.user,
            status__in=['SCHEDULED', 'CONFIRMED', 'IN_PROGRESS'],
            is_emergency=False
        ).order_by('appointment_date', 'appointment_time')
    else:
        appointments = Appointment.objects.filter(
            is_emergency=False
        ).order_by('appointment_date', 'appointment_time')
    
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
                # 0. Check DoctorStatus for real-time status (leave, off-duty)
                try:
                    vet = User.objects.get(pk=vet_id)
                    doctor_status = DoctorStatus.objects.filter(veterinarian=vet).first()
                    if doctor_status:
                        # Check if on leave for the appointment date
                        if doctor_status.leave_start and doctor_status.leave_end:
                            if doctor_status.leave_start <= appointment_date <= doctor_status.leave_end:
                                messages.error(request, f'Dr. {vet.get_full_name()} is on leave from {doctor_status.leave_start} to {doctor_status.leave_end}.')
                                return redirect('appointments:book')
                        
                        # For same-day bookings, also check if doctor is off-duty
                        if appointment_date == date.today():
                            if doctor_status.status == 'OFF_DUTY':
                                messages.warning(request, f'Dr. {vet.get_full_name()} is currently off-duty. Appointment booked but may need confirmation.')
                            elif doctor_status.status == 'ON_LEAVE':
                                messages.error(request, f'Dr. {vet.get_full_name()} is on leave today.')
                                return redirect('appointments:book')
                except User.DoesNotExist:
                    pass
                
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

            # Analyze the reason text to determine priority using AI Bridge
            reason_text = request.POST.get('reason', '')
            
            # Use Groq AI for symptom analysis
            ai_result = analyze_symptoms_with_groq(reason_text)
            priority_level = ai_result.get('priority', 'NORMAL')
            priority_reason = ai_result.get('reason', 'Standard appointment')
            ai_category = ai_result.get('category', 'Routine')
            
            # If emergency priority detected, mark as emergency
            is_emergency = priority_level == 'EMERGENCY'
            
            appointment = Appointment.objects.create(
                pet_id=pet_id,
                owner=request.user,
                veterinarian_id=vet_id if vet_id else None,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                duration=int(request.POST.get('duration', 30)),
                reason=reason_text,
                priority=priority_level,
                is_emergency=is_emergency,
                created_by=request.user
            )

            # Create an EmergencyCase record if it's an emergency
            if is_emergency:
                # Determine severity based on keywords in reason
                reason_lower = reason_text.lower()

                # CRITICAL - Life-threatening, immediate intervention needed
                critical_keywords = [
                    'not breathing', 'cant breathe', "can't breathe", 'unconscious',
                    'unresponsive', 'not moving', 'cold body', 'seizure', 'collapsed',
                    'no heartbeat', 'cardiac arrest',
                    'blue gums', 'blue tongue', 'severe bleeding', 'heavy bleeding',
                    'poisoned', 'rat poison', 'antifreeze', 'chocolate poisoning',
                    'hit by car', 'trauma', 'drowning', 'electrocution',
                    'pale gums', 'shock', 'anemia', 'weak', 'weakness',
                    'vomiting for two days', 'not eating for', 'prolonged anorexia',
                    'severe dehydration', 'internal hemorrhage', 'bleeding from mouth',
                    'status epilepticus', 'gastric dilatation', 'volvulus'
                ]

                # SEVERE - Serious but may not be immediately life-threatening
                severe_keywords = [
                    'vomiting blood', 'bloody diarrhea', 'heat stroke',
                    'snake bite', 'spider bite', 'bee sting', 'anaphylaxis',
                    'bloat', 'twisted stomach', 'difficulty breathing',
                    'paralyzed', 'cant walk', "can't walk", 'limping badly',
                    'swelling rapidly', 'swollen face', 'throat swelling',
                    'urinary blockage', 'cant urinate', "can't urinate",
                    'broken bone', 'fracture', 'deep wound', 'open fracture',
                    'near drowning', 'aspiration pneumonia'
                ]

                if any(kw in reason_lower for kw in critical_keywords):
                    severity = 'CRITICAL'
                elif any(kw in reason_lower for kw in severe_keywords):
                    severity = 'SEVERE'
                else:
                    severity = 'MODERATE'

                EmergencyCase.objects.create(
                    appointment=appointment,
                    pet=appointment.pet,
                    owner=appointment.owner,
                    severity=severity,
                    symptoms=reason_text,
                    situation_description=f"AI-detected emergency from booking.\n\nCategory: {ai_category}\nReason: {priority_reason}\nModel: {ai_result.get('model', 'unknown')}",
                    assigned_vet=appointment.veterinarian
                )
                messages.warning(
                    request, 
                    f'EMERGENCY DETECTED! Your appointment has been marked as high priority. '
                    f'AI Assessment: {priority_reason}. Please seek immediate veterinary care if needed.'
                )
            elif priority_level == 'HIGH':
                messages.info(
                    request,
                    f'Your appointment has been marked as URGENT priority. AI Assessment: {priority_reason}'
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
    
    # Get doctors currently on leave or off-duty
    doctors_on_leave = DoctorStatus.objects.filter(
        status__in=['ON_LEAVE', 'OFF_DUTY']
    ).select_related('veterinarian')
    
    # Get all doctor statuses for display
    all_doctor_statuses = DoctorStatus.objects.all().select_related('veterinarian')
    
    # Get clinic settings
    clinic_settings = ClinicSettings.objects.first()
    
    # Build a list of ALL vets with their status for the sidebar
    # Doctors without DoctorStatus records default to "Available"
    vet_status_list = []
    status_lookup = {status.veterinarian.id: status for status in all_doctor_statuses}
    for vet in veterinarians:
        if vet.id in status_lookup:
            status = status_lookup[vet.id]
            vet_status_list.append({
                'veterinarian': vet,
                'status': status.status,
                'status_display': status.get_status_display(),
                'leave_start': status.leave_start,
                'leave_end': status.leave_end,
            })
        else:
            # Default to Available for doctors without explicit status
            vet_status_list.append({
                'veterinarian': vet,
                'status': 'AVAILABLE',
                'status_display': 'Available',
                'leave_start': None,
                'leave_end': None,
            })
    
    # Build doctor status info for JavaScript
    # Include ALL vets - those without DoctorStatus are treated as AVAILABLE
    doctor_status_data = {}
    
    # First, add all vets as available by default
    for vet in veterinarians:
        doctor_status_data[str(vet.id)] = {
            'status': 'AVAILABLE',
            'status_display': 'Available',
            'on_leave': False,
            'leave_start': None,
            'leave_end': None,
            'available_for_booking': True,
        }
    
    # Then override with actual status for those who have DoctorStatus records
    for status in all_doctor_statuses:
        doctor_status_data[str(status.veterinarian.id)] = {
            'status': status.status,
            'status_display': status.get_status_display(),
            'on_leave': status.is_on_leave_today(),
            'leave_start': status.leave_start.isoformat() if status.leave_start else None,
            'leave_end': status.leave_end.isoformat() if status.leave_end else None,
            'available_for_booking': status.is_available_for_booking(),
        }
    
    return render(request, 'appointments/book.html', {
        'pets': pets,
        'veterinarians': veterinarians,
        'today': today,
        'unavailable_dates': unavailable_dates,
        'unavailable_days': unavailable_days,
        'doctors_on_leave': doctors_on_leave,
        'all_doctor_statuses': all_doctor_statuses,
        'vet_status_list': vet_status_list,
        'clinic_settings': clinic_settings,
        'doctor_status_json': json.dumps(doctor_status_data),
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
        # Store pet name before deleting
        pet_name = case.pet.name

        # Also finish the linked appointment if it exists
        if case.appointment:
            case.appointment.status = 'COMPLETED'
            case.appointment.is_emergency = False
            case.appointment.priority = 'NORMAL'
            case.appointment.save()

        # Delete the emergency case (it will no longer appear anywhere)
        case.delete()

        messages.success(request, f'Emergency case for {pet_name} resolved and removed from queue.')
    else:
        messages.error(request, 'You do not have permission to resolve this case.')

    # Redirect to vet dashboard or queue with cleared notification
    return redirect('appointments:queue_status')

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
    """View emergency cases"""
    if request.user.is_staff:
        # Admins see all unassigned + assigned emergencies
        cases = EmergencyCase.objects.filter(
            status__in=['WAITING', 'IN_TREATMENT']
        ).order_by('severity', 'reported_at')
    elif request.user.role == 'VET':
        # Veterinarians see:
        # 1. Emergencies assigned to them
        # 2. Unassigned emergencies (so they can claim them)
        cases = EmergencyCase.objects.filter(
            status__in=['WAITING', 'IN_TREATMENT']
        ).filter(
            models.Q(assigned_vet=request.user) | models.Q(assigned_vet=None)
        ).order_by('severity', 'reported_at')
    else:
        cases = EmergencyCase.objects.none()
    
    return render(request, 'appointments/emergency.html', {'cases': cases})


@login_required
def claim_emergency(request, pk):
    """Claim an unassigned emergency case"""
    emergency = get_object_or_404(EmergencyCase, pk=pk)
    
    # Only vets can claim, and only unassigned cases
    if request.user.role != 'VET':
        messages.error(request, 'Only veterinarians can claim emergency cases.')
        return redirect('appointments:emergency')
    
    if emergency.assigned_vet is not None:
        messages.warning(request, 'This emergency is already assigned to another doctor.')
        return redirect('appointments:emergency')
    
    # Claim the emergency
    emergency.assigned_vet = request.user
    emergency.status = 'IN_TREATMENT'
    emergency.save()
    
    messages.success(request, f'You have claimed the emergency case for {emergency.pet.name}.')
    return redirect('appointments:emergency')


# ============== NEW VIEWS FOR ENHANCED FEATURES ==============

@login_required
def queue_status(request):
    """View current queue status and waiting times - FIFO ordering"""
    from .models import QueueStatus, ClinicSettings
    
    today = timezone.now().date()
    queue = QueueStatus.get_today_status()
    
    # Get ALL today's appointments (not just active ones)
    all_today_appointments = Appointment.objects.filter(appointment_date=today)
    
    # Calculate statistics dynamically
    total_appointments = all_today_appointments.count()
    completed_count = all_today_appointments.filter(status='COMPLETED').count()
    cancelled_count = all_today_appointments.filter(status='CANCELLED').count()
    waiting_count = all_today_appointments.filter(
        status__in=['SCHEDULED', 'CONFIRMED', 'IN_PROGRESS'],
        is_emergency=False
    ).count()
    
    # Get today's active appointments (FIFO: by token_number first, then by appointment_time)
    # Exclude completed and cancelled appointments
    today_appointments = Appointment.objects.filter(
        appointment_date=today,
        status__in=['SCHEDULED', 'CONFIRMED', 'IN_PROGRESS'],
        is_emergency=False  # Emergencies handled separately
    ).order_by('token_number', 'appointment_time', 'created_at')
    
    # Get active emergencies (FIFO by reported_at)
    active_emergencies = EmergencyCase.objects.filter(
        status__in=['WAITING', 'IN_TREATMENT']
    ).order_by('reported_at')
    
    # Get clinic settings
    try:
        clinic = ClinicSettings.objects.first()
    except:
        clinic = None
    
    # Calculate waiting info for current user's appointments
    user_appointments = []
    if request.user.is_pet_owner:
        user_appointments = today_appointments.filter(owner=request.user)
        for apt in user_appointments:
            if apt.token_number:
                apt.pets_ahead = max(0, apt.token_number - queue.last_called_token - 1)
                apt.estimated_wait = queue.get_estimated_wait_time(apt.token_number)
            else:
                apt.pets_ahead = 0
                apt.estimated_wait = 0
    
    # Update queue object with dynamic values
    queue.total_appointments = total_appointments
    queue.completed_appointments = completed_count
    
    return render(request, 'appointments/queue_status.html', {
        'queue': queue,
        'today_appointments': today_appointments,
        'active_emergencies': active_emergencies,
        'user_appointments': user_appointments,
        'clinic': clinic,
        'total_appointments': total_appointments,
        'waiting_count': waiting_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
    })


@login_required
def queue_api(request):
    """API endpoint for live queue status - returns JSON"""
    from .models import QueueStatus, ClinicSettings
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    queue = QueueStatus.get_today_status()
    
    # Get ALL today's appointments for statistics
    all_today_appointments = Appointment.objects.filter(appointment_date=today)
    
    # Calculate statistics dynamically
    total_appointments = all_today_appointments.count()
    completed_count = all_today_appointments.filter(status='COMPLETED').count()
    waiting_count = all_today_appointments.filter(
        status__in=['SCHEDULED', 'CONFIRMED', 'IN_PROGRESS'],
        is_emergency=False
    ).count()
    
    # Get today's active appointments for the queue
    today_appointments = Appointment.objects.filter(
        appointment_date=today,
        status__in=['SCHEDULED', 'CONFIRMED', 'IN_PROGRESS'],
        is_emergency=False
    ).order_by('token_number', 'appointment_time', 'created_at')
    
    # Get active emergencies
    active_emergencies = EmergencyCase.objects.filter(
        status__in=['WAITING', 'IN_TREATMENT']
    ).order_by('reported_at')
    
    # Build appointments data
    appointments_data = []
    for apt in today_appointments:
        # Calculate wait time
        wait_time = None
        if apt.status == 'IN_PROGRESS':
            # Show how long they've been in checking
            if apt.updated_at:
                wait_minutes = int((timezone.now() - apt.updated_at).total_seconds() / 60)
                wait_time = f"{wait_minutes} min"
        elif apt.token_number and apt.status == 'CONFIRMED':
            # Show estimated wait
            if queue.last_called_token:
                tokens_ahead = max(0, apt.token_number - queue.last_called_token - 1)
                avg_time = queue.avg_wait_time or 15
                wait_minutes = tokens_ahead * avg_time
                wait_time = f"~{wait_minutes} min"
        
        appointments_data.append({
            'id': apt.id,
            'pet_name': apt.pet.name,
            'owner_name': apt.owner.get_full_name(),
            'token_number': apt.token_number,
            'appointment_time': apt.appointment_time.strftime('%H:%M'),
            'status': apt.status,
            'status_display': apt.get_status_display(),
            'reason': apt.reason[:50] if apt.reason else '',
            'wait_time': wait_time,
            'is_current': apt.status == 'IN_PROGRESS',
        })
    
    # Build emergencies data
    emergencies_data = []
    for ec in active_emergencies:
        emergencies_data.append({
            'id': ec.id,
            'pet_name': ec.pet.name,
            'owner_name': ec.owner.get_full_name(),
            'severity': ec.severity,
            'severity_display': ec.get_severity_display(),
            'status': ec.status,
            'status_display': ec.get_status_display(),
            'symptoms': ec.symptoms[:100] if ec.symptoms else '',
            'assigned_vet': ec.assigned_vet.get_full_name() if ec.assigned_vet else None,
            'reported_at': ec.reported_at.strftime('%H:%M'),
        })
    
    return JsonResponse({
        'success': True,
        'queue': {
            'last_called_token': queue.last_called_token,
            'total_appointments': total_appointments,
            'completed_appointments': completed_count,
            'waiting_count': waiting_count,
            'avg_wait_time': queue.avg_wait_time or 15,
        },
        'appointments': appointments_data,
        'emergencies': emergencies_data,
        'timestamp': timezone.now().isoformat(),
    })


@login_required
def check_in(request, pk):
    """Check in for an appointment and get token number"""
    from .models import QueueStatus
    
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Permission check
    if request.user != appointment.owner and not request.user.is_staff:
        messages.error(request, 'You do not have permission to check in for this appointment.')
        return redirect('appointments:list')
    
    # Generate token number
    queue = QueueStatus.get_today_status()
    
    if not appointment.token_number:
        appointment.token_number = queue.get_next_token()
        appointment.check_in_time = timezone.now()
        appointment.status = 'CONFIRMED'
        appointment.save()
        
        # Update queue totals
        queue.total_appointments = Appointment.objects.filter(
            appointment_date=timezone.now().date(),
            status__in=['SCHEDULED', 'CONFIRMED', 'IN_PROGRESS']
        ).count()
        queue.save()
        
        messages.success(request, f'Checked in successfully! Your token number is #{appointment.token_number}')
    else:
        messages.info(request, f'Already checked in. Your token number is #{appointment.token_number}')
    
    return redirect('appointments:queue_status')


@login_required 
def call_next_patient(request):
    """For vets/staff to call the next patient in queue"""
    from .models import QueueStatus
    
    if not request.user.is_veterinarian and not request.user.is_staff:
        messages.error(request, 'Only veterinarians can call patients.')
        return redirect('appointments:list')
    
    queue = QueueStatus.get_today_status()
    today = timezone.now().date()
    
    # Find next appointment in queue
    next_appointment = Appointment.objects.filter(
        appointment_date=today,
        status='CONFIRMED',
        token_number__gt=queue.last_called_token
    ).order_by('token_number').first()
    
    if next_appointment:
        queue.last_called_token = next_appointment.token_number
        queue.save()
        
        next_appointment.status = 'IN_PROGRESS'
        next_appointment.save()
        
        # Update doctor status if exists
        try:
            from .models import DoctorStatus
            doctor_status, _ = DoctorStatus.objects.get_or_create(veterinarian=request.user)
            doctor_status.status = 'BUSY'
            doctor_status.current_appointment = next_appointment
            doctor_status.save()
        except:
            pass
        
        messages.success(request, f'Calling Token #{next_appointment.token_number} - {next_appointment.pet.name}')
    else:
        messages.info(request, 'No more patients in queue.')
    
    return redirect('appointments:queue_status')


@login_required
def doctor_status_view(request):
    """View and manage doctor statuses"""
    from .models import DoctorStatus
    
    # Get all doctors with their current status
    doctors = User.objects.filter(role='VET', is_active=True)
    
    doctor_info = []
    for doctor in doctors:
        status, created = DoctorStatus.objects.get_or_create(
            veterinarian=doctor,
            defaults={'status': 'OFF_DUTY'}
        )
        doctor_info.append({
            'doctor': doctor,
            'status': status,
            'is_available': status.is_available_for_booking(),
        })
    
    return render(request, 'appointments/doctor_status.html', {'doctors': doctor_info})


@login_required
def update_doctor_status(request):
    """Update current doctor's status"""
    from .models import DoctorStatus
    
    if not request.user.is_veterinarian:
        messages.error(request, 'Only veterinarians can update their status.')
        return redirect('appointments:list')
    
    if request.method == 'POST':
        status_value = request.POST.get('status')
        status_message = request.POST.get('status_message', '')
        leave_start = request.POST.get('leave_start')
        leave_end = request.POST.get('leave_end')
        leave_reason = request.POST.get('leave_reason', '')
        
        doctor_status, created = DoctorStatus.objects.get_or_create(veterinarian=request.user)
        doctor_status.status = status_value
        doctor_status.status_message = status_message
        
        if status_value == 'ON_LEAVE' and leave_start and leave_end:
            doctor_status.leave_start = datetime.strptime(leave_start, '%Y-%m-%d').date()
            doctor_status.leave_end = datetime.strptime(leave_end, '%Y-%m-%d').date()
            doctor_status.leave_reason = leave_reason
        
        doctor_status.save()
        messages.success(request, 'Status updated successfully!')
        
    return redirect('appointments:doctor_status')


# ============== GROOMING VIEWS ==============

@login_required
def grooming_services(request):
    """View available grooming services"""
    from .models import GroomingService
    
    services = GroomingService.objects.filter(is_active=True)
    return render(request, 'appointments/grooming/services.html', {'services': services})


@login_required
def book_grooming(request):
    """Book a grooming appointment"""
    from .models import GroomingService, GroomingAppointment, ClinicSettings
    
    if request.method == 'POST':
        try:
            pet_id = request.POST.get('pet')
            service_ids = request.POST.getlist('services')
            pet_size = request.POST.get('pet_size', 'MEDIUM')
            appointment_date = datetime.strptime(request.POST.get('appointment_date'), '%Y-%m-%d').date()
            appointment_time = datetime.strptime(request.POST.get('appointment_time'), '%H:%M').time()
            special_instructions = request.POST.get('special_instructions', '')
            
            # Check if clinic is open
            clinic = ClinicSettings.objects.first()
            if clinic and not clinic.is_clinic_open(appointment_date):
                messages.error(request, 'The clinic is closed on this date.')
                return redirect('appointments:book_grooming')
            
            # Create grooming appointment
            appointment = GroomingAppointment.objects.create(
                pet_id=pet_id,
                owner=request.user,
                pet_size=pet_size,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                special_instructions=special_instructions,
                created_by=request.user,
            )
            
            # Add selected services
            for service_id in service_ids:
                appointment.services.add(service_id)
            
            # Calculate price after adding services
            appointment.total_price = appointment.calculate_total_price()
            appointment.save()
            
            messages.success(request, f'Grooming appointment booked for {appointment_date}!')
            return redirect('appointments:grooming_list')
            
        except Exception as e:
            messages.error(request, f'Error booking grooming: {str(e)}')
    
    pets = Pet.objects.filter(owner=request.user) if request.user.is_pet_owner else Pet.objects.all()
    services = GroomingService.objects.filter(is_active=True)
    today = date.today()
    
    return render(request, 'appointments/grooming/book.html', {
        'pets': pets,
        'services': services,
        'today': today,
    })


@login_required
def grooming_list(request):
    """List grooming appointments"""
    from .models import GroomingAppointment
    
    if request.user.is_pet_owner:
        appointments = GroomingAppointment.objects.filter(owner=request.user)
    else:
        appointments = GroomingAppointment.objects.all()
    
    return render(request, 'appointments/grooming/list.html', {'appointments': appointments})


@login_required
def cancel_grooming(request, pk):
    """Cancel a grooming appointment"""
    from .models import GroomingAppointment
    
    appointment = get_object_or_404(GroomingAppointment, pk=pk)
    
    if request.user == appointment.owner or request.user.is_staff:
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, 'Grooming appointment cancelled.')
    else:
        messages.error(request, 'Permission denied.')
    
    return redirect('appointments:grooming_list')


# ============================================================================
# AI BRIDGE API ENDPOINTS
# ============================================================================

from django.views.decorators.http import require_http_methods
import json as json_lib


@login_required
@require_http_methods(["POST"])
def api_analyze_symptoms(request):
    """
    API endpoint to analyze symptoms using Groq AI.
    
    POST /appointments/api/analyze-symptoms/
    Body: {"symptoms": "text description", "pet_id": "optional"}
    
    Returns: {"status": "success", "priority": "EMERGENCY/HIGH/NORMAL/LOW", ...}
    """
    from .ai_bridge import analyze_symptoms_with_groq, format_symptom_response
    
    try:
        data = json_lib.loads(request.body)
        symptoms = data.get('symptoms', '')
        pet_id = data.get('pet_id', None)
        
        if not symptoms:
            return JsonResponse({
                'status': 'error',
                'message': 'No symptoms provided'
            }, status=400)
        
        # Call AI bridge
        result = analyze_symptoms_with_groq(symptoms, pet_id)
        response = format_symptom_response(result)
        
        return JsonResponse(response)
        
    except json_lib.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_analyze_image(request):
    """
    API endpoint to analyze skin image using PyTorch model.
    
    POST /appointments/api/analyze-image/
    Body: multipart/form-data with 'image' file
    
    Returns: {"status": "success", "disease": "...", "confidence": "...", ...}
    """
    from .ai_bridge import analyze_skin_image, format_image_response
    import tempfile
    import os
    
    try:
        if 'image' not in request.FILES:
            return JsonResponse({
                'status': 'error',
                'message': 'No image provided'
            }, status=400)
        
        image = request.FILES['image']
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            for chunk in image.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        
        try:
            # Call AI bridge
            result = analyze_skin_image(tmp_path)
            response = format_image_response(result)
            return JsonResponse(response)
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def api_check_priority(request):
    """
    Quick API to check priority from GET request (for AJAX form validation).
    
    GET /appointments/api/check-priority/?symptoms=...
    
    Returns: {"priority": "NORMAL", "category": "Routine", "reason": "..."}
    """
    from .ai_bridge import analyze_symptoms_with_groq
    
    symptoms = request.GET.get('symptoms', '')
    
    if not symptoms:
        return JsonResponse({
            'priority': 'NORMAL',
            'category': 'Routine',
            'reason': 'No symptoms provided'
        })
    
    result = analyze_symptoms_with_groq(symptoms)
    
    return JsonResponse({
        'priority': result.get('priority', 'NORMAL'),
        'category': result.get('category', 'Routine'),
        'reason': result.get('reason', ''),
        'is_emergency': result.get('priority') == 'EMERGENCY'
    })
