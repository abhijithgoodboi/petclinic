# Database Schema Documentation

## Overview

The Veterinary Workflow Platform uses a relational database with the following main components:

## Entity Relationship Diagram

```
User (accounts)
  ├── VeterinarianProfile
  ├── PetOwnerProfile
  ├── Pet (owner)
  ├── Appointment (owner, veterinarian)
  └── MedicalRecord (veterinarian)

Pet (medical_records)
  ├── MedicalRecord
  ├── Vaccination
  ├── SkinDiseaseImage
  └── MedicalDocument

Appointment (appointments)
  ├── EmergencyCase
  └── AppointmentFeedback
```

## Tables

### accounts_user
Extended Django User model with role-based access.

**Fields:**
- id (PK)
- username
- email
- password
- first_name
- last_name
- role (ADMIN, VET, OWNER, RECEPTIONIST)
- phone_number
- address
- date_of_birth
- profile_picture
- is_active_account
- created_at
- updated_at

### accounts_veterinarianprofile
Additional information for veterinarians.

**Fields:**
- id (PK)
- user_id (FK → User)
- license_number (unique)
- specialization
- years_of_experience
- qualifications
- consultation_fee
- bio
- available_for_emergency
- rating
- total_consultations

### medical_records_pet
Pet information and basic medical data.

**Fields:**
- id (PK)
- owner_id (FK → User)
- name
- species (DOG, CAT, BIRD, etc.)
- breed
- gender
- date_of_birth
- color
- weight
- microchip_id (unique)
- photo
- allergies
- medical_conditions
- special_notes
- is_active

### medical_records_medicalrecord
Complete medical history for each visit.

**Fields:**
- id (PK)
- pet_id (FK → Pet)
- veterinarian_id (FK → User)
- visit_date
- visit_type
- symptoms
- diagnosis
- treatment
- notes
- temperature
- heart_rate
- respiratory_rate
- weight
- follow_up_required
- follow_up_date

### medical_records_prescription
Prescriptions associated with medical records.

**Fields:**
- id (PK)
- medical_record_id (FK → MedicalRecord)
- medication_name
- dosage
- frequency
- duration
- instructions

### medical_records_vaccination
Vaccination records and schedules.

**Fields:**
- id (PK)
- pet_id (FK → Pet)
- vaccine_name
- disease_protection
- scheduled_date
- administered_date
- next_due_date
- status
- veterinarian_id (FK → User)
- batch_number
- manufacturer
- notes

### appointments_doctoravailability
Doctor's weekly availability schedule.

**Fields:**
- id (PK)
- veterinarian_id (FK → User)
- day_of_week (0-6)
- start_time
- end_time
- is_available
- max_appointments

### appointments_appointment
Appointment bookings.

**Fields:**
- id (PK)
- pet_id (FK → Pet)
- owner_id (FK → User)
- veterinarian_id (FK → User)
- appointment_date
- appointment_time
- end_time
- duration
- status
- priority
- is_emergency
- reason
- notes
- confirmation_sent
- reminder_sent

### appointments_emergencycase
Emergency case tracking and prioritization.

**Fields:**
- id (PK)
- appointment_id (FK → Appointment, nullable)
- pet_id (FK → Pet)
- owner_id (FK → User)
- severity
- symptoms
- situation_description
- assigned_vet_id (FK → User)
- status
- treatment_started_at
- treatment_completed_at
- queue_number
- wait_time_minutes
- triage_notes
- treatment_notes

### ai_diagnosis_skindiseaseimage
Uploaded images for AI analysis.

**Fields:**
- id (PK)
- pet_id (FK → Pet)
- uploaded_by_id (FK → User)
- image
- description
- affected_area
- status
- processing_started_at
- processing_completed_at
- image_width
- image_height
- file_size

### ai_diagnosis_diagnosisresult
AI prediction results.

**Fields:**
- id (PK)
- skin_disease_image_id (FK → SkinDiseaseImage)
- predicted_disease
- confidence_score
- confidence_level
- alternative_diagnosis_1/2/3
- alternative_confidence_1/2/3
- model_version
- processing_time_seconds
- recommended_actions
- urgency_level
- reviewed_by_vet_id (FK → User)
- vet_confirmed
- vet_diagnosis
- vet_notes
- reviewed_at

### ai_diagnosis_treatmentrecommendation
Treatment information database.

**Fields:**
- id (PK)
- disease (unique)
- description
- symptoms
- causes
- home_care
- medical_treatment
- prevention
- recovery_time
- contagious

## Indexes

Performance indexes are created on:
- appointment_date + appointment_time
- status fields
- is_emergency flag
- Foreign key relationships

## Constraints

- Unique constraints on license_number, microchip_id
- Foreign key constraints with appropriate CASCADE/SET_NULL
- Check constraints on time ranges (end_time > start_time)

## Database Migrations

All schema changes are managed through Django migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Sample Queries

### Get all upcoming appointments for a user
```sql
SELECT * FROM appointments_appointment
WHERE owner_id = 1
AND appointment_date >= CURRENT_DATE
ORDER BY appointment_date, appointment_time;
```

### Get pets with overdue vaccinations
```sql
SELECT p.*, v.vaccine_name, v.scheduled_date
FROM medical_records_pet p
JOIN medical_records_vaccination v ON p.id = v.pet_id
WHERE v.status = 'OVERDUE';
```

### Get emergency cases by severity
```sql
SELECT ec.*, p.name as pet_name
FROM appointments_emergencycase ec
JOIN medical_records_pet p ON ec.pet_id = p.id
WHERE ec.status IN ('WAITING', 'IN_TREATMENT')
ORDER BY 
  CASE ec.severity
    WHEN 'CRITICAL' THEN 1
    WHEN 'SEVERE' THEN 2
    WHEN 'MODERATE' THEN 3
    WHEN 'MILD' THEN 4
  END,
  ec.reported_at;
```
