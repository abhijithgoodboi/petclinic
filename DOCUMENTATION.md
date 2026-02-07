# Ernakulam Pet Hospital - Veterinary Management System

## Complete Documentation

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Installation & Setup](#installation--setup)
4. [Django Apps](#django-apps)
5. [AI Integration](#ai-integration)
6. [Database Models](#database-models)
7. [User Roles & Permissions](#user-roles--permissions)
8. [API Endpoints](#api-endpoints)
9. [Frontend Features](#frontend-features)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)

---

## Project Overview

**Ernakulam Pet Hospital** is a full-featured veterinary clinic management system built with Django. It provides:

- **User Management**: Pet owners, veterinarians, and administrators
- **Pet Records**: Complete pet profiles with medical history
- **Appointment Booking**: Online booking with AI-powered priority detection
- **Emergency Handling**: Automatic emergency case creation
- **AI Skin Disease Detection**: PyTorch-based image analysis
- **Grooming Services**: Separate booking for grooming appointments
- **Medical Records**: Prescriptions, vaccinations, and documents

### Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 5.1+ |
| Database | SQLite (dev) / PostgreSQL (prod) |
| AI - Symptoms | Groq AI (LLaMA 3.3 70B) |
| AI - Images | PyTorch (ResNet50) |
| Frontend | Django Templates + Bootstrap 5 |
| Python | 3.14 |

---

## System Architecture

```
veterinary_platform/
|
|-- accounts/           # User management & authentication
|-- appointments/       # Appointment booking & queue system
|-- ai_diagnosis/       # AI skin disease detection
|-- medical_records/    # Pet records, prescriptions, vaccinations
|-- vet_workflow/       # Main Django project settings
|
|-- templates/          # HTML templates
|-- static/             # CSS, JS, images
|-- media/              # User uploads
|-- venv/               # Python virtual environment
|
|-- best_model_cat.pth  # PyTorch model weights (90MB)
|-- manage.py           # Django management
|-- requirements.txt    # Python dependencies
```

---

## Installation & Setup

### Prerequisites

- Python 3.11+
- pip
- virtualenv (recommended)

### Quick Start

```bash
# Clone the repository
cd /home/anastasia/gits/veterinary_platform

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install PyTorch (CPU version)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install Groq
pip install groq

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Access the Application

- **Main Site**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **AI Diagnosis**: http://127.0.0.1:8000/ai/
- **Appointments**: http://127.0.0.1:8000/appointments/

---

## Django Apps

### 1. accounts

Handles user authentication and role-based access control.

**Models:**
- `User` - Extended Django user with roles (ADMIN, VET, OWNER)
- `VeterinarianProfile` - Additional vet info (license, specialization, fees)
- `PetOwnerProfile` - Emergency contacts, preferred vet

**Key Features:**
- Role-based permissions
- Social authentication support (via django-allauth)
- Profile management

### 2. appointments

Manages appointment booking, queue system, and emergency cases.

**Models:**
- `ClinicSettings` - Working hours, off days, slot duration
- `ClinicHoliday` - Specific closure dates
- `DoctorStatus` - Real-time availability (available, busy, on leave)
- `DoctorAvailability` - Weekly schedule
- `Appointment` - Main appointment model with priority levels
- `EmergencyCase` - Emergency tracking with severity levels
- `GroomingService` - Available grooming services
- `GroomingAppointment` - Grooming bookings
- `QueueStatus` - Daily token/queue management
- `AppointmentFeedback` - Post-visit ratings

**Key Features:**
- AI-powered priority detection via Groq
- Automatic emergency case creation
- Custom calendar with Sunday closures
- Doctor leave date blocking
- Token-based queue system

### 3. ai_diagnosis

AI-powered skin disease detection using PyTorch.

**Models:**
- `SkinDiseaseImage` - Uploaded images for analysis
- `DiagnosisResult` - AI predictions with confidence scores
- `TreatmentRecommendation` - Disease treatment database
- `AIModelMetrics` - Model performance tracking

**Key Features:**
- ResNet50-based image classification
- 4 disease categories: Ringworm, Mange, Flea Allergy, Healthy
- Vet review/confirmation workflow
- Treatment recommendations

### 4. medical_records

Complete medical history management.

**Models:**
- `Pet` - Pet profiles (species, breed, allergies)
- `MedicalRecord` - Visit records with vitals
- `Prescription` - Medication details
- `Vaccination` - Vaccine schedules and records
- `MedicalDocument` - X-rays, lab reports, etc.

---

## AI Integration

### 1. Groq AI - Symptom Analysis

**Purpose:** Analyze symptom text to determine appointment priority.

**Location:** `appointments/ai_bridge.py`

**How it works:**
1. User enters symptoms in "Reason for Visit"
2. Text is sent to Groq AI (LLaMA 3.3 70B)
3. AI classifies as: Emergency / Urgent / Routine
4. Priority is mapped: EMERGENCY / HIGH / NORMAL / LOW
5. If EMERGENCY, auto-creates EmergencyCase

**Usage:**
```python
from appointments.ai_bridge import analyze_symptoms_with_groq

result = analyze_symptoms_with_groq("dog not breathing, blue gums")
# Returns: {'priority': 'EMERGENCY', 'reason': 'Life-threatening respiratory distress'}
```

**API Key:** Stored in `appointments/ai_bridge.py` (line 31)

### 2. PyTorch - Skin Disease Detection

**Purpose:** Analyze pet skin images to detect diseases.

**Location:** `ai_diagnosis/ai_model.py`

**Model Details:**
- Architecture: ResNet50 (pretrained, fine-tuned)
- Model File: `best_model_cat.pth` (90MB)
- Input: 224x224 RGB image
- Output: 4 classes

**Disease Classes:**
| Model Class | Database Code | Display Name |
|-------------|---------------|--------------|
| Flea_Allergy | FLEA | Flea Allergy Dermatitis |
| Health | HEALTHY | Healthy - No Disease |
| Ringworm | RINGWORM | Ringworm (Dermatophytosis) |
| Scabies | MANGE | Scabies (Sarcoptic Mange) |

**Usage:**
```python
from ai_diagnosis.ai_model import analyze_skin_image

result = analyze_skin_image("/path/to/image.jpg")
# Returns: {'primary_disease': 'RINGWORM', 'primary_confidence': 0.9969, ...}
```

**External Script:**
```bash
# Direct CLI usage
python ai_diagnosis/scripts/analyze_image.py cat.jpg
# Returns JSON with prediction
```

### 3. AI Bridge (Unified Interface)

**Location:** `appointments/ai_bridge.py`

Provides a unified interface for both AI systems:

```python
from appointments.ai_bridge import get_full_assessment

result = get_full_assessment(
    symptoms="dog scratching, hair loss",
    image_path="/path/to/skin_image.jpg",
    pet_id="123"
)
# Combines both symptom and image analysis
```

---

## Database Models

### User Model (accounts.User)

```python
class User(AbstractUser):
    USER_ROLES = ('ADMIN', 'VET', 'OWNER')
    role = CharField(max_length=20)
    phone_number = CharField(max_length=17)
    address = TextField()
    date_of_birth = DateField()
    profile_picture = ImageField()
```

### Pet Model (medical_records.Pet)

```python
class Pet(Model):
    PET_SPECIES = ('DOG', 'CAT', 'BIRD', 'RABBIT', 'OTHER')
    owner = ForeignKey(User)
    name = CharField(max_length=100)
    species = CharField(max_length=20)
    breed = CharField(max_length=100)
    gender = CharField(max_length=1)  # M/F
    date_of_birth = DateField()
    weight = DecimalField()  # kg
    allergies = TextField()
    medical_conditions = TextField()
```

### Appointment Model (appointments.Appointment)

```python
class Appointment(Model):
    STATUS_CHOICES = ('SCHEDULED', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'NO_SHOW')
    PRIORITY_LEVELS = ('LOW', 'NORMAL', 'HIGH', 'EMERGENCY')
    
    pet = ForeignKey(Pet)
    owner = ForeignKey(User)
    veterinarian = ForeignKey(User)
    appointment_date = DateField()
    appointment_time = TimeField()
    status = CharField(max_length=20)
    priority = CharField(max_length=20)
    is_emergency = BooleanField()
    reason = TextField()
    token_number = IntegerField()
```

### DiagnosisResult Model (ai_diagnosis.DiagnosisResult)

```python
class DiagnosisResult(Model):
    DISEASE_CATEGORIES = ('RINGWORM', 'MANGE', 'DERMATITIS', 'HOT_SPOT', 
                          'ALLERGY', 'FUNGAL', 'BACTERIAL', 'FLEA', 'ECZEMA', 'HEALTHY')
    
    skin_disease_image = OneToOneField(SkinDiseaseImage)
    predicted_disease = CharField(max_length=50)
    confidence_score = FloatField()  # 0-1
    confidence_level = CharField()  # VERY_LOW to VERY_HIGH
    model_version = CharField(max_length=50)
    urgency_level = CharField()  # ROUTINE, SOON, URGENT, EMERGENCY
    
    # Vet review
    reviewed_by_vet = ForeignKey(User)
    vet_confirmed = BooleanField()
    vet_diagnosis = CharField()
    vet_notes = TextField()
```

---

## User Roles & Permissions

### 1. Administrator (ADMIN)
- Full access to all features
- Manage users, vets, clinic settings
- View all appointments and records
- Access admin panel

### 2. Veterinarian (VET)
- View assigned appointments
- Update appointment status
- Create medical records
- Review AI diagnoses (confirm/override)
- Manage own schedule

### 3. Pet Owner (OWNER)
- Register pets
- Book appointments
- Upload skin images for AI analysis
- View own pets' medical records
- Provide feedback

---

## API Endpoints

### Symptom Analysis
```
POST /appointments/api/analyze-symptoms/
Content-Type: application/json

{
    "symptoms": "dog not eating, vomiting"
}

Response:
{
    "priority": "HIGH",
    "category": "Urgent",
    "reason": "Gastrointestinal distress requires prompt attention"
}
```

### Image Analysis
```
POST /appointments/api/analyze-image/
Content-Type: multipart/form-data

image: <file>

Response:
{
    "disease": "RINGWORM",
    "disease_name": "Ringworm (Dermatophytosis)",
    "confidence": "99.69%",
    "treatment": {...}
}
```

### Priority Check
```
GET /appointments/api/check-priority/?symptoms=dog+bleeding

Response:
{
    "priority": "EMERGENCY",
    "is_emergency": true
}
```

---

## Frontend Features

### Custom Appointment Calendar

**Location:** `templates/appointments/book.html`

Features:
- Pure JavaScript (no external libraries)
- Sundays shown in **red with strikethrough** (clinic closed)
- Doctor leave dates shown in **yellow** and disabled
- Past dates grayed out and disabled
- Blue theme matching site design
- Legend explaining color codes

### AI Diagnosis Result Page

**Location:** `templates/ai_diagnosis/result.html`

Features:
- Displays primary diagnosis with confidence bar
- Shows urgency level
- Emergency alert if applicable
- Vet review form (for VET users)
- Treatment recommendations
- Book appointment button

---

## Testing

### Run All Tests
```bash
python manage.py test
```

### Test AI Model Directly
```bash
# Activate virtual environment
source venv/bin/activate

# Test PyTorch skin disease model
python ai_diagnosis/scripts/analyze_image.py cat.jpg

# Expected output:
# {"primary_disease": "RINGWORM", "primary_confidence": 0.9969, ...}
```

### Test Groq Symptom Analysis
```bash
python manage.py shell -c "
from appointments.ai_bridge import analyze_symptoms_with_groq
result = analyze_symptoms_with_groq('dog not breathing')
print(f'Priority: {result[\"priority\"]}')"

# Expected: Priority: EMERGENCY
```

### Test Symptom Scenarios

| Symptom | Expected Priority |
|---------|-------------------|
| "dog not breathing, blue gums" | EMERGENCY |
| "cat hit by car, bleeding heavily" | EMERGENCY |
| "vomiting for 2 days, very weak" | EMERGENCY |
| "limping after walk" | HIGH/URGENT |
| "annual vaccination" | NORMAL |
| "mild scratching" | LOW/NORMAL |

---

## Troubleshooting

### PyTorch Model Not Loading
```bash
# Check if model file exists
ls -la best_model_cat.pth

# Check PyTorch installation
python -c "import torch; print(torch.__version__)"

# Check model loading
python manage.py shell -c "
from ai_diagnosis.ai_model import is_model_loaded, get_model_info
print(get_model_info())"
```

### Groq API Errors
1. Check API key in `appointments/ai_bridge.py`
2. Check internet connection
3. Fallback uses keyword-based analysis in `appointments/priority_analyzer.py`

### Database Issues
```bash
# Reset migrations (development only)
python manage.py migrate --run-syncdb

# Check database
python manage.py dbshell
```

### Static Files Not Loading
```bash
python manage.py collectstatic
```

---

## File Reference

| File | Purpose |
|------|---------|
| `accounts/models.py` | User, VetProfile, OwnerProfile |
| `appointments/models.py` | Appointment, EmergencyCase, Queue |
| `appointments/views.py` | Booking views, API endpoints |
| `appointments/ai_bridge.py` | Unified AI interface (Groq + PyTorch) |
| `appointments/priority_analyzer.py` | Keyword-based fallback |
| `ai_diagnosis/models.py` | SkinDiseaseImage, DiagnosisResult |
| `ai_diagnosis/ai_model.py` | PyTorch ResNet50 detector |
| `ai_diagnosis/scripts/analyze_image.py` | CLI image analysis |
| `medical_records/models.py` | Pet, MedicalRecord, Vaccination |
| `templates/appointments/book.html` | Custom calendar UI |
| `templates/ai_diagnosis/result.html` | Diagnosis result page |
| `best_model_cat.pth` | Trained PyTorch model weights |

---

## Environment Variables

Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
GROQ_API_KEY=gsk_...
```

---

## Contact & Support

- **Project**: Ernakulam Pet Hospital
- **Platform**: Django Veterinary Management System
- **Version**: 1.0.0
- **Python**: 3.14

---

*Last Updated: February 2026*
