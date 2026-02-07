# Veterinary Workflow Automation Platform

A comprehensive web-based veterinary clinic management system built with Django and SQL database.

## Features

### 1. **Doctor Availability Management**
- Doctors can set their available time slots
- Schedule management with day-wise availability
- Real-time availability checking

### 2. **Appointment Management**
- Book appointments for pets
- Automatic doctor assignment based on availability
- Appointment status tracking (Scheduled, Completed, Cancelled)
- Appointment history

### 3. **Emergency Prioritization**
- Mark appointments as emergency cases
- Automatic priority queue management
- Emergency case dashboard for quick access

### 4. **Vaccination Tracking**
- Complete vaccination records for pets
- Due date tracking and reminders
- Vaccination history

### 5. **Medical Records**
- Comprehensive medical history for each pet
- Diagnosis, treatment, and prescription records
- Visit history tracking
- Document uploads (X-rays, lab reports, etc.)

### 6. **AI-Based Skin Disease Detection**
- Upload pet images for analysis
- AI-powered skin disease prediction for dogs and cats
- Disease confidence scores
- Treatment recommendations

### 7. **User Management**
- Role-based access (Admin, Veterinarian, Pet Owner, Receptionist)
- User authentication and authorization
- Profile management

## Tech Stack

- **Backend**: Django 5.1+
- **Database**: PostgreSQL/MySQL/SQLite
- **AI/ML**: TensorFlow/PyTorch for image analysis
- **Frontend**: Django Templates with Bootstrap 5
- **Image Processing**: Pillow, OpenCV
- **API**: Django REST Framework (optional)

## Installation

### Prerequisites
```bash
Python 3.8+
pip
virtualenv
PostgreSQL or MySQL (optional, SQLite for development)
```

### Setup Instructions

1. **Clone the repository**
```bash
cd ~/gits
git clone <repository-url> veterinary_platform
cd veterinary_platform
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure database**
Edit `vet_workflow/settings.py` and update the DATABASES configuration:

For PostgreSQL:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'vet_workflow_db',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

For MySQL:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'vet_workflow_db',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

5. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Load initial data (optional)**
```bash
python manage.py loaddata initial_data.json
```

8. **Run the development server**
```bash
python manage.py runserver
```

9. **Access the application**
- Application: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/

## Project Structure

```
veterinary_platform/
├── manage.py
├── requirements.txt
├── README.md
├── vet_workflow/          # Main project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/              # User management
│   ├── models.py         # User profiles, roles
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── templates/
├── appointments/          # Appointment management
│   ├── models.py         # Appointment, Availability
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── templates/
├── medical_records/       # Medical records & vaccinations
│   ├── models.py         # Pet, MedicalRecord, Vaccination
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── templates/
├── ai_diagnosis/          # AI skin disease detection
│   ├── models.py         # DiagnosisResult
│   ├── views.py
│   ├── ai_model.py       # ML model integration
│   ├── forms.py
│   ├── urls.py
│   └── templates/
├── static/               # Static files (CSS, JS, images)
├── media/                # Uploaded files
└── templates/            # Base templates
```

## Database Schema

### Key Models

#### User Models (accounts app)
- **UserProfile**: Extended user information with role
- **VeterinarianProfile**: Veterinarian-specific information

#### Appointment Models (appointments app)
- **DoctorAvailability**: Doctor's available time slots
- **Appointment**: Appointment bookings
- **EmergencyCase**: Emergency case tracking

#### Medical Records Models (medical_records app)
- **Pet**: Pet information
- **MedicalRecord**: Medical history entries
- **Vaccination**: Vaccination records
- **Prescription**: Prescription details

#### AI Diagnosis Models (ai_diagnosis app)
- **SkinDiseaseImage**: Uploaded images for analysis
- **DiagnosisResult**: AI prediction results

## Usage

### For Pet Owners
1. Register and create a profile
2. Add your pets
3. Book appointments
4. View medical history
5. Upload images for AI diagnosis
6. Track vaccinations

### For Veterinarians
1. Set availability schedule
2. View assigned appointments
3. Manage medical records
4. Write prescriptions
5. Review AI diagnosis results
6. Handle emergency cases

### For Administrators
1. Manage users and roles
2. System configuration
3. View analytics and reports
4. Manage clinic operations

## AI Model Integration

The AI skin disease detection module uses a pre-trained deep learning model to identify common skin diseases in dogs and cats.

### Supported Conditions
- Ringworm
- Mange
- Dermatitis
- Hot spots
- Allergic reactions
- Fungal infections
- Bacterial infections

### Model Training
To train your own model, see `ai_diagnosis/model_training/README.md`

## API Documentation

REST API endpoints are available at `/api/`

For detailed API documentation, visit `/api/docs/` when the server is running.

## Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test appointments

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## Deployment

### Production Settings
1. Set `DEBUG = False` in settings.py
2. Configure `ALLOWED_HOSTS`
3. Use environment variables for sensitive data
4. Configure static file serving
5. Set up proper database backups
6. Configure email settings for notifications

### Using Docker
```bash
docker-compose up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub or contact support@veterinaryplatform.com

## Authors

- Your Name - Initial work

## Acknowledgments

- Django community
- TensorFlow/PyTorch teams
- All contributors
