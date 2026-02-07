# Testing Guide

## Manual Testing Checklist

### 1. User Registration and Authentication

#### Test Cases:
- [ ] Register new pet owner account
- [ ] Register new veterinarian account  
- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] Logout functionality
- [ ] Password reset flow
- [ ] Profile view and edit

#### Steps:
```
1. Navigate to /accounts/register/
2. Fill registration form
3. Submit and verify success message
4. Login with new credentials
5. Access profile page
6. Update profile information
7. Logout
```

### 2. Pet Management

#### Test Cases:
- [ ] Add new pet
- [ ] View pet list
- [ ] View pet details
- [ ] Edit pet information
- [ ] Upload pet photo
- [ ] Add allergies and medical notes

#### Steps:
```
1. Login as pet owner
2. Navigate to "My Pets"
3. Click "Add Pet"
4. Fill pet details:
   - Name: "Max"
   - Species: Dog
   - Breed: "Golden Retriever"
   - DOB: 2020-01-15
   - Weight: 25.5 kg
5. Upload photo
6. Save and verify
```

### 3. Doctor Availability

#### Test Cases:
- [ ] Set weekly availability
- [ ] Edit availability schedule
- [ ] View availability calendar
- [ ] Mark unavailable days

#### Steps:
```
1. Login as veterinarian
2. Navigate to "Availability"
3. Set schedule:
   - Monday: 9:00 AM - 5:00 PM
   - Tuesday: 9:00 AM - 5:00 PM
   - Wednesday: 9:00 AM - 12:00 PM
   - Thursday: OFF
   - Friday: 9:00 AM - 5:00 PM
4. Save schedule
5. Verify in calendar view
```

### 4. Appointment Booking

#### Test Cases:
- [ ] Book regular appointment
- [ ] Book emergency appointment
- [ ] View appointment list
- [ ] Cancel appointment
- [ ] Reschedule appointment
- [ ] Check conflict detection

#### Steps:
```
1. Login as pet owner
2. Navigate to "Book Appointment"
3. Select pet: Max
4. Select date: Tomorrow
5. View available time slots
6. Select veterinarian
7. Enter reason: "Regular checkup"
8. Submit booking
9. Verify confirmation email
10. View in appointment list
```

### 5. Emergency Case Management

#### Test Cases:
- [ ] Create emergency case
- [ ] Assign severity level
- [ ] View emergency queue
- [ ] Assign to veterinarian
- [ ] Update case status
- [ ] Complete emergency treatment

#### Steps:
```
1. Login as receptionist/vet
2. Navigate to "Emergency Cases"
3. Create new case:
   - Pet: Max
   - Severity: SEVERE
   - Symptoms: "Not eating, lethargic"
   - Description: "Owner reports 24hr"
4. Verify queue number assigned
5. Assign to available vet
6. Update status to "IN_TREATMENT"
7. Add treatment notes
8. Mark as "RESOLVED"
```

### 6. Medical Records

#### Test Cases:
- [ ] Create medical record
- [ ] Add vital signs
- [ ] Add diagnosis and treatment
- [ ] Create prescription
- [ ] Upload medical documents
- [ ] Schedule follow-up

#### Steps:
```
1. Login as veterinarian
2. Select appointment
3. Create medical record:
   - Visit type: Regular Checkup
   - Symptoms: "Coughing"
   - Diagnosis: "Kennel cough"
   - Treatment: "Rest and medication"
   - Temperature: 101.5°F
   - Heart rate: 80 BPM
4. Add prescription:
   - Medication: "Amoxicillin"
   - Dosage: "250mg"
   - Frequency: "Twice daily"
   - Duration: "7 days"
5. Upload X-ray image
6. Schedule follow-up for 1 week
7. Save record
```

### 7. Vaccination Management

#### Test Cases:
- [ ] Schedule vaccination
- [ ] Record administered vaccine
- [ ] View vaccination history
- [ ] Check overdue vaccinations
- [ ] Update vaccination status

#### Steps:
```
1. Navigate to "Vaccinations"
2. Schedule new vaccination:
   - Pet: Max
   - Vaccine: "Rabies"
   - Date: Next month
   - Disease protection: "Rabies"
3. When administered:
   - Update status to "COMPLETED"
   - Add batch number
   - Add manufacturer
   - Set next due date
4. Verify in vaccination history
```

### 8. AI Diagnosis

#### Test Cases:
- [ ] Upload valid image
- [ ] Upload invalid file type
- [ ] Process image analysis
- [ ] View diagnosis results
- [ ] View confidence scores
- [ ] Check alternative diagnoses
- [ ] View treatment recommendations
- [ ] Veterinarian review

#### Steps:
```
1. Login as pet owner
2. Navigate to "AI Diagnosis"
3. Click "Upload Image"
4. Select pet: Max
5. Upload skin image (JPG/PNG)
6. Add description: "Red patch on leg"
7. Submit for analysis
8. Wait for processing
9. View results:
   - Primary diagnosis
   - Confidence score
   - Alternative diagnoses
   - Treatment recommendations
   - Urgency level
10. Verify vet can review and confirm
```

### 9. Admin Panel

#### Test Cases:
- [ ] Access admin dashboard
- [ ] Manage users
- [ ] View appointments
- [ ] Monitor emergency cases
- [ ] Review AI predictions
- [ ] Generate reports

#### Steps:
```
1. Login as admin
2. Navigate to /admin/
3. View dashboard statistics
4. Test user management:
   - Create user
   - Edit user
   - Change user role
5. View appointment calendar
6. Monitor emergency queue
7. Review AI model metrics
```

### 10. Search and Filtering

#### Test Cases:
- [ ] Search pets by name
- [ ] Filter appointments by date
- [ ] Filter by status
- [ ] Search medical records
- [ ] Filter by veterinarian

## Automated Testing

### Unit Tests

Create test file: `appointments/tests.py`

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from medical_records.models import Pet
from .models import Appointment, DoctorAvailability

User = get_user_model()

class AppointmentModelTests(TestCase):
    def setUp(self):
        # Create test users
        self.owner = User.objects.create_user(
            username='owner1',
            password='testpass123',
            role='OWNER'
        )
        self.vet = User.objects.create_user(
            username='vet1',
            password='testpass123',
            role='VET'
        )
        
        # Create test pet
        self.pet = Pet.objects.create(
            owner=self.owner,
            name='Buddy',
            species='DOG',
            breed='Labrador',
            gender='M',
            date_of_birth='2020-01-01',
            weight=30.0
        )
    
    def test_appointment_creation(self):
        """Test basic appointment creation"""
        appointment = Appointment.objects.create(
            pet=self.pet,
            owner=self.owner,
            veterinarian=self.vet,
            appointment_date='2024-12-31',
            appointment_time='10:00',
            reason='Checkup'
        )
        self.assertEqual(appointment.status, 'SCHEDULED')
        self.assertFalse(appointment.is_emergency)
    
    def test_emergency_appointment_priority(self):
        """Test emergency appointments get high priority"""
        appointment = Appointment.objects.create(
            pet=self.pet,
            owner=self.owner,
            veterinarian=self.vet,
            appointment_date='2024-12-31',
            appointment_time='10:00',
            reason='Emergency',
            is_emergency=True
        )
        self.assertEqual(appointment.priority, 'EMERGENCY')
```

### Run Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test appointments

# Run with verbosity
python manage.py test --verbosity=2

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## Performance Testing

### Load Testing with Apache Bench

```bash
# Test home page
ab -n 1000 -c 10 http://127.0.0.1:8000/

# Test appointment list
ab -n 500 -c 5 -C "sessionid=your_session_id" http://127.0.0.1:8000/appointments/

# Expected results:
# - Response time < 200ms
# - No failed requests
# - Consistent performance
```

### Database Query Optimization

```python
# Check for N+1 queries
from django.db import connection
from django.test.utils import override_settings

@override_settings(DEBUG=True)
def test_appointment_list_queries():
    # Clear queries
    connection.queries_log.clear()
    
    # Execute view
    response = client.get('/appointments/')
    
    # Check query count
    num_queries = len(connection.queries)
    print(f"Number of queries: {num_queries}")
    
    # Should be < 10 for optimized view
    assert num_queries < 10
```

## Security Testing

### Authentication Tests

```python
def test_login_required(self):
    """Test views require authentication"""
    response = self.client.get('/appointments/')
    self.assertEqual(response.status_code, 302)  # Redirect to login
    
def test_role_based_access(self):
    """Test veterinarian-only views"""
    self.client.login(username='owner1', password='testpass123')
    response = self.client.get('/appointments/emergency/')
    self.assertEqual(response.status_code, 403)  # Forbidden
```

### File Upload Security

```python
def test_image_upload_validation(self):
    """Test only valid image files accepted"""
    # Try uploading .exe file
    with open('test.exe', 'rb') as f:
        response = self.client.post('/ai-diagnosis/upload/', {
            'pet': self.pet.id,
            'image': f
        })
    self.assertContains(response, 'Invalid file type')
```

## Integration Testing

### Full Workflow Test

```python
class AppointmentWorkflowTest(TestCase):
    def test_complete_appointment_flow(self):
        """Test full appointment workflow"""
        # 1. Owner books appointment
        self.client.login(username='owner1', password='testpass123')
        response = self.client.post('/appointments/book/', {
            'pet': self.pet.id,
            'appointment_date': '2024-12-31',
            'appointment_time': '10:00',
            'veterinarian': self.vet.id,
            'reason': 'Checkup'
        })
        self.assertEqual(response.status_code, 302)
        
        # 2. Vet views appointment
        self.client.login(username='vet1', password='testpass123')
        response = self.client.get('/appointments/')
        self.assertContains(response, 'Buddy')
        
        # 3. Vet creates medical record
        appointment = Appointment.objects.first()
        response = self.client.post(f'/medical/records/create/', {
            'appointment': appointment.id,
            'symptoms': 'Healthy',
            'diagnosis': 'Normal',
            'treatment': 'None needed'
        })
        self.assertEqual(response.status_code, 302)
        
        # 4. Verify appointment marked complete
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'COMPLETED')
```

## Browser Testing

### Browsers to Test:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Chrome
- [ ] Mobile Safari

### Features to Test per Browser:
- Page rendering
- Form submission
- File uploads
- JavaScript functionality
- Responsive design
- Print functionality

## Regression Testing

After each update, test:
- [ ] User authentication
- [ ] Appointment booking
- [ ] Medical record creation
- [ ] AI image upload
- [ ] Admin functions
- [ ] API endpoints

## Bug Reporting Template

```markdown
**Title:** Brief description

**Environment:**
- OS: Ubuntu 22.04
- Browser: Chrome 120
- Django: 5.1.0

**Steps to Reproduce:**
1. Login as pet owner
2. Navigate to appointments
3. Click "Book Appointment"
4. ...

**Expected Behavior:**
Appointment should be created

**Actual Behavior:**
Error 500 displayed

**Screenshots:**
[Attach screenshot]

**Console Errors:**
```
[Paste console output]
```

**Priority:** High/Medium/Low
```

## Test Coverage Goals

- **Models:** 90%+ coverage
- **Views:** 80%+ coverage
- **Forms:** 85%+ coverage
- **Overall:** 80%+ coverage

## Continuous Testing

Set up pre-commit hooks:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run tests
python manage.py test

# Check for test failures
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi

# Run linting
flake8 .

echo "All tests passed!"
exit 0
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

**Remember:** Test early, test often, automate everything!
