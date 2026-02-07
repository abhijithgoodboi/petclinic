# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       CLIENT LAYER                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   Web    │  │  Mobile  │  │   API    │  │  Admin   │  │
│  │ Browser  │  │  (Future)│  │ Clients  │  │  Panel   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
└───────┼─────────────┼─────────────┼─────────────┼─────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                          │
┌─────────────────────────┼─────────────────────────────────┐
│                    WEB SERVER                              │
│              Nginx / Apache (Production)                   │
│            Django Dev Server (Development)                 │
└─────────────────────────┼─────────────────────────────────┘
                          │
┌─────────────────────────┼─────────────────────────────────┐
│                   APPLICATION LAYER                        │
│                      Django 5.1+                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              URL Router (urls.py)                   │  │
│  └───────┬──────────┬──────────┬──────────┬────────────┘  │
│          │          │          │          │                │
│  ┌───────▼──┐ ┌────▼────┐ ┌──▼────┐ ┌───▼──────┐        │
│  │Accounts  │ │Appoint  │ │Medical│ │AI        │        │
│  │  App     │ │ments    │ │Records│ │Diagnosis │        │
│  │          │ │  App    │ │  App  │ │  App     │        │
│  │─────────│ │─────────│ │───────│ │──────────│        │
│  │Views    │ │Views    │ │Views  │ │Views     │        │
│  │Models   │ │Models   │ │Models │ │Models    │        │
│  │Forms    │ │Forms    │ │Forms  │ │AI Model  │        │
│  └─────────┘ └─────────┘ └───────┘ └──────────┘        │
│                          │                                │
└──────────────────────────┼────────────────────────────────┘
                          │
┌─────────────────────────┼─────────────────────────────────┐
│                    DATA LAYER                              │
│  ┌──────────────────┐   │   ┌─────────────────────────┐  │
│  │   Database       │◄──┘   │   File Storage         │  │
│  │ PostgreSQL/MySQL │       │   Media Files          │  │
│  │    SQLite        │       │   Static Files         │  │
│  └──────────────────┘       │   AI Model Files       │  │
│                             └─────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Application Flow

### 1. User Authentication Flow
```
User → Login Page → Django Auth → Create Session → Redirect to Dashboard
                      ↓
                   Verify Role
                      ↓
        ┌─────────────┼─────────────┐
        │             │             │
    Admin       Veterinarian    Pet Owner
        │             │             │
   All Access    Vet Dashboard  Owner Dashboard
```

### 2. Appointment Booking Flow
```
Pet Owner → Select Pet → Choose Date → View Available Slots
                                            ↓
                                    Check Vet Availability
                                            ↓
                                    Select Time Slot
                                            ↓
                                    Confirm Booking
                                            ↓
                            ┌──────────────┴──────────────┐
                            ↓                             ↓
                    Save Appointment               Send Notifications
                            ↓                             ↓
                    Update Schedule                Email Confirmation
```

### 3. AI Diagnosis Flow
```
Pet Owner → Upload Image → Validate Format → Save to Database
                                    ↓
                            Trigger AI Processing
                                    ↓
                        ┌───────────┴───────────┐
                        ↓                       ↓
            Preprocess Image            Load AI Model
              (Resize, Normalize)              ↓
                        ↓               Run Prediction
                        └───────────┬───────────┘
                                   ↓
                        Calculate Confidence Score
                                   ↓
                        Get Top 3 Predictions
                                   ↓
                      Fetch Treatment Recommendations
                                   ↓
                        Save DiagnosisResult
                                   ↓
                        Display Results to User
                                   ↓
                     Notify Veterinarian for Review
```

### 4. Emergency Case Flow
```
Emergency Call → Create EmergencyCase → Assign Severity Level
                                             ↓
                                   Assign Queue Number
                                             ↓
                           Notify Available Veterinarians
                                             ↓
                              Assign to Veterinarian
                                             ↓
                              Update Status: IN_TREATMENT
                                             ↓
                              Complete Treatment
                                             ↓
                           Create Medical Record
                                             ↓
                              Update Status: RESOLVED
```

## Component Interactions

### User Management
```
┌──────────────┐
│     User     │
└──────┬───────┘
       │
   ┌───┴────┬────────┬──────────┐
   │        │        │          │
   ▼        ▼        ▼          ▼
Owner     Vet    Admin    Receptionist
Profile  Profile
   │        │
   ▼        ▼
  Pets   Availability
```

### Medical Records System
```
┌──────────┐
│   Pet    │
└────┬─────┘
     │
  ┌──┴───────┬────────────┬─────────────┐
  │          │            │             │
  ▼          ▼            ▼             ▼
Medical  Vaccination  Documents    Appointments
Records
  │
  └──► Prescriptions
```

### AI Diagnosis System
```
┌────────────────┐
│ SkinDiseaseImg │
└───────┬────────┘
        │
        ▼
┌───────────────┐      ┌────────────┐
│ AI Processor  │◄────►│  AI Model  │
└───────┬───────┘      └────────────┘
        │
        ▼
┌───────────────┐      ┌─────────────────┐
│DiagnosisResult│◄────►│Treatment Recomm │
└───────┬───────┘      └─────────────────┘
        │
        ▼
┌───────────────┐
│Vet Review     │
└───────────────┘
```

## Data Flow Patterns

### Read Operation
```
User Request → View → Model.objects.get() → Database → Return Data
                                                          ↓
                                                    Template Render
                                                          ↓
                                                    HTML Response
```

### Write Operation
```
User Form → View → Form Validation → Model.save() → Database
                        ↓                              ↓
                   Error Check                    Success
                        ↓                              ↓
                   Show Errors                   Redirect + Message
```

### File Upload
```
User Upload → View → Validate File → Save to Media Directory
                        ↓                    ↓
                   Check Size         Update Model with Path
                   Check Type               ↓
                        ↓              Save to Database
                   Return Status
```

## Security Layers

```
┌─────────────────────────────────────────────┐
│         HTTPS/SSL Encryption                │
└────────────────┬────────────────────────────┘
                 │
┌────────────────┼────────────────────────────┐
│         Authentication Layer                │
│   (Session, Token, Password Hash)           │
└────────────────┬────────────────────────────┘
                 │
┌────────────────┼────────────────────────────┐
│         Authorization Layer                 │
│   (Role-based Access Control)               │
└────────────────┬────────────────────────────┘
                 │
┌────────────────┼────────────────────────────┐
│         CSRF Protection                     │
│         XSS Protection                      │
│         SQL Injection Prevention            │
└────────────────┬────────────────────────────┘
                 │
┌────────────────┼────────────────────────────┐
│         Input Validation                    │
│         File Type Validation                │
└─────────────────────────────────────────────┘
```

## Scalability Design

### Horizontal Scaling
```
Load Balancer
     │
  ┌──┴───┬───────┬───────┐
  │      │       │       │
Web 1  Web 2  Web 3  Web N
  │      │       │       │
  └──┬───┴───────┴───────┘
     │
  Database + Cache
     │
  File Storage
```

### Caching Strategy
```
Request → Check Cache → Cache Hit? → Return Cached Data
                          │
                          NO
                          ↓
                    Query Database
                          ↓
                    Store in Cache
                          ↓
                    Return Fresh Data
```

## Deployment Architecture

### Development
```
Developer → Git → Local Django Server → SQLite
                       ↓
                  Static Files
                  Media Files
```

### Production
```
Git Repo → CI/CD Pipeline → Application Server (Gunicorn)
                                     ↓
                            Load Balancer (Nginx)
                                     ↓
                          ┌──────────┴──────────┐
                          ↓                     ↓
                    Web Server 1         Web Server 2
                          ↓                     ↓
                          └──────────┬──────────┘
                                     ↓
                            Database Server (PostgreSQL)
                                     ↓
                            File Storage (S3/Local)
```

## Technology Stack Layers

```
┌─────────────────────────────────────────────┐
│         Presentation Layer                  │
│    HTML, CSS (Bootstrap), JavaScript        │
└────────────────┬────────────────────────────┘
                 │
┌────────────────┼────────────────────────────┐
│         Application Layer                   │
│           Django 5.1+                       │
│         Python 3.8+                         │
└────────────────┬────────────────────────────┘
                 │
┌────────────────┼────────────────────────────┐
│         Business Logic Layer                │
│     Models, Views, Forms                    │
│     AI Processing Module                    │
└────────────────┬────────────────────────────┘
                 │
┌────────────────┼────────────────────────────┐
│         Data Access Layer                   │
│         Django ORM                          │
└────────────────┬────────────────────────────┘
                 │
┌────────────────┼────────────────────────────┐
│         Database Layer                      │
│  PostgreSQL / MySQL / SQLite                │
└─────────────────────────────────────────────┘
```

## Integration Points

### External Systems
```
Veterinary Platform
        │
  ┌─────┴─────────┬──────────────┬─────────────┐
  │               │              │             │
Email          Payment      SMS Service   Cloud Storage
Provider      Gateway                     (Future)
```

### API Integration
```
Mobile App  →  REST API  ←  Third-party Services
                   ↓
            Django Backend
                   ↓
            Database
```

This architecture ensures:
- ✅ Scalability
- ✅ Maintainability  
- ✅ Security
- ✅ Performance
- ✅ Extensibility
