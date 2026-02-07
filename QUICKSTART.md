# Quick Start Guide

## Installation (5 minutes)

### 1. Clone and Setup

```bash
cd ~/gits/veterinary_platform
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Create virtual environment
- Install dependencies
- Create directories
- Setup database
- Create .env file

### 2. Configure Database (Optional)

By default, SQLite is used. To use PostgreSQL or MySQL:

Edit `.env` file and uncomment database settings:
```env
DB_NAME=vet_workflow_db
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432  # or 3306 for MySQL
```

Then edit `vet_workflow/settings.py` and uncomment the PostgreSQL or MySQL section.

### 3. Run Migrations

```bash
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Start Development Server

```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000/

## First Steps

### 1. Access Admin Panel
- URL: http://127.0.0.1:8000/admin/
- Login with superuser credentials

### 2. Create Test Data

#### Create a Veterinarian:
1. Go to Users → Add User
2. Fill details, set role as "Veterinarian"
3. Create Veterinarian Profile for this user

#### Create a Pet Owner:
1. Register via the website or admin
2. Set role as "Pet Owner"

#### Add a Pet:
1. Login as pet owner
2. Go to "My Pets" → "Add Pet"
3. Fill pet details

#### Set Doctor Availability:
1. Login as veterinarian
2. Go to "Appointments" → "Availability"
3. Set available time slots

### 3. Book an Appointment

1. Login as pet owner
2. Go to "Appointments" → "Book Appointment"
3. Select pet, date, time, and veterinarian
4. Submit booking

### 4. Upload Image for AI Diagnosis

1. Login as pet owner
2. Go to "AI Diagnosis" → "Upload"
3. Select pet and upload image
4. View AI prediction results

## Project Structure

```
veterinary_platform/
├── accounts/              # User authentication & profiles
├── appointments/          # Appointment management
├── medical_records/       # Pets & medical records
├── ai_diagnosis/          # AI skin disease detection
├── vet_workflow/          # Main project settings
├── templates/             # HTML templates
├── static/               # CSS, JS, images
├── media/                # Uploaded files
├── manage.py             # Django management
├── requirements.txt      # Python dependencies
├── setup.sh             # Setup script
└── README.md            # Documentation
```

## Key Features

### 1. User Management
- Role-based access (Admin, Vet, Owner, Receptionist)
- Profile management
- Authentication & authorization

### 2. Appointment System
- Online booking
- Doctor availability management
- Emergency prioritization
- Status tracking
- Email notifications

### 3. Medical Records
- Pet profiles
- Medical history
- Prescriptions
- Document uploads
- Vital signs tracking

### 4. Vaccination Tracking
- Schedule vaccinations
- Due date reminders
- Vaccination history
- Status tracking

### 5. AI Diagnosis
- Upload pet images
- AI-powered skin disease detection
- Confidence scores
- Treatment recommendations
- Veterinarian review

### 6. Emergency Management
- Priority queue system
- Severity levels
- Real-time status updates
- Triage notes

## API Endpoints (Optional)

If using Django REST Framework:

- `/api/appointments/` - Appointment list/create
- `/api/pets/` - Pet list/create
- `/api/medical-records/` - Medical records
- `/api/ai-diagnosis/` - AI diagnosis results

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test

# Open Django shell
python manage.py shell
```

## Troubleshooting

### Issue: Module not found
```bash
pip install -r requirements.txt
```

### Issue: Database errors
```bash
python manage.py makemigrations
python manage.py migrate
```

### Issue: Static files not loading
```bash
python manage.py collectstatic --clear
```

### Issue: Permission denied
```bash
chmod +x setup.sh
```

## Next Steps

1. ✅ Complete initial setup
2. ✅ Create test users and data
3. ✅ Explore admin interface
4. ✅ Test appointment booking
5. ✅ Try AI diagnosis feature
6. 📖 Read full documentation
7. 🚀 Deploy to production

## Support

- Documentation: See README.md
- Issues: Create GitHub issue
- Email: support@vetworkflow.com

## License

MIT License - See LICENSE file
