# Changelog

All notable changes to this project will be documented in this file.

## [2026-01-28]

### Fixed
- **AI Diagnosis View:** Fixed a `SyntaxError` in `ai_diagnosis/views.py` caused by duplicated code and incorrect placeholders. The `diagnosis_result` and `review_diagnosis` views are now clean and functional.
- **Vaccination Scheduling:** Fixed a bug where scheduling a vaccination failed with a `str' and 'datetime.date'` comparison error.
- **Pet List Display:** Fixed a bug where the pet cards were not rendering in the patient list. The loop has been restored, and Rocky (and all other pets) will now correctly appear in the "My Pets" or "Patients" view.
- **Emergency Case Handling:** Fixed a `NameError` where `EmergencyCase` was not imported in the account views, causing the profile page to crash for veterinarians.
- **Doctor Availability:** Improved the booking validation logic. The system now allows bookings by default if a doctor hasn't set a schedule, but strictly honors "Not Available" markers and specific time ranges if they have been defined.
- **Appointment Booking:** Fixed a bug where booking an appointment failed with `unsupported type for timedelta minutes component: str`. The duration is now correctly converted to an integer before saving.

### Added
- **Eyecandy Booking UI:** Redesigned the appointment reservation interface with a modern multi-column form, icon-integrated inputs, and a polished UI switch for emergencies.
- **Eyecandy Appointment UI:** Redesigned the appointment list with modern cards.
- **Eyecandy Availability UI:** Upgraded the doctor roster with a polished, card-wrapped table and subtle badge-based shift tracking.
- **Eyecandy AI Landing Page:** Redesigned the AI Diagnosis home page.
- **Eyecandy AI Upload UI:** Completely redesigned the AI image upload interface.
- **Eyecandy AI History UI:** Upgraded the AI Diagnosis History page with modern cards.
- **Native Windows Support:** Added `setup.bat` and `run.bat` to provide a seamless experience for Windows users.
- **Full System Backup:** Created a comprehensive project backup.
- **Setup Automation:** Overhauled `setup.sh` to install all dependencies (OpenCV, TensorFlow, etc.) directly from `requirements.txt` and automatically generate a rebranded VetCare environment.
- **Custom Medical Record Form:** Replaced the Django Admin entry form with a high-quality frontend form. Veterinarians can now document visits, vital signs, and treatment plans directly within the app's main interface.
- **Patients Section for Doctors:** Veterinarians now have a dedicated "Patients" link in the navbar and a card on their home dashboard to access the complete clinic pet database.
- **Quick Medical Documentation:** Added an "Add Record" button to the pet profile for doctors, streamlining the process of creating visit notes.
- **Vaccination Management for Vets:** Veterinarians can now schedule new vaccinations and "administer" existing ones with a single click from the pet's profile.
- **Top-Right Gradient Focal Point:** Implemented a global lighting effect where the primary brand gradient originates from the top-right corner of every page. This adds depth and a modern "Eyecandy" feel to the entire platform.
- **Eyecandy UI Overhaul:** Massive visual upgrade across the entire platform.
    - **Typography:** Switched to the **Inter** font family for a cleaner, modern look.
    - **Glassmorphism:** Implemented real-time backdrop-blur effects on the navigation bar.
    - **Modern Hero Section:** Redesigned the homepage with animated background elements, high-contrast typography, and stylized badges.
    - **Gradient Icons:** Dashboard icons now feature beautiful multi-color gradients.
    - **Refined Transitions:** Added global CSS transitions for theme switching and button interactions.
    - **Enhanced Cards:** Switched to borderless, soft-shadow cards for a more "app-like" feel.
- **Theme-Aware Calendar:** The **Flatpickr** calendar now perfectly matches the selected theme (Light, Dark, or Decay). Backgrounds, text colors, and selection highlights now adapt dynamically.
- **Visual Calendar Availability:** Replaced the standard date input with **Flatpickr**. The calendar now dynamically colors dates: **Green** for available slots and **Red** for unavailable ones based on the selected doctor's schedule.
- **Project Backup:** Created a compressed backup of the entire codebase (`veterinary_platform_backup.tar.gz`) before implementing major UI changes.
- **Delete Availability:** Veterinarians and staff can now delete specific availability records from the list.
- **Strengthened Availability Enforcement:** The "Book Appointment" button is now automatically disabled if the selected doctor is unavailable or if the time is outside their working hours.
- **Unavailable Dates Sidebar:** Added a sidebar to the booking page that lists upcoming dates and recurring days when veterinarians have explicitly marked themselves as unavailable.
- **Real-time Availability Check:** The appointment booking page now dynamically shows the selected doctor's availability (working hours or if they are off) as soon as the user selects a date and veterinarian.
- **Decay Theme:** Added a custom "Decay" theme (muted greens and deep dark backgrounds) as part of the theme cycle. The theme toggle now cycles through Light -> Dark -> Decay.
- **Theme Toggle:** Integrated a light/dark mode toggle in the navigation bar using Bootstrap 5.3's built-in theme support. User preference is persisted in local storage.
- **Integrated Admin Dashboard:** Created a new frontend admin panel for administrators to view global statistics (users, pets, appointments, AI diagnoses) and manage the system.
- **Admin Registration:** Users can now register as an "Administrator" directly. This automatically grants them staff and superuser permissions.
- **Appointment Token System:** Veterinarians now see appointments numbered as "Token #1", "Token #2", etc., based on their daily schedule.

### Changed
- **Registration Security:** Removed the "Administrator" role from the public registration form. Administrative accounts must now be created by existing superusers, preventing unauthorized global access.
- **Login Security Polish:** Removed all demo credentials and instructional cards from the public login page.
- **Python Version Locking:** Explicitly migrated and locked the entire platform to **Python 3.11**. The `setup.sh` script now prioritizes and requires the `python3.11` binary to ensure AI library compatibility.
- **Rebranding:** Renamed the platform from "VetWorkflow" to **"VetCare"**. Updated the brand name in the navigation bar, footer, and homepage hero section.
- **Global Back Button:** Expanded the visibility of the "Back" button. It is now available on every page (including Login and Registration) for all users, not just those who are logged in.
- **Restricted Emergency Visibility:** Veterinarians now only see emergency cases specifically assigned to them in their queue, dashboard alerts, and profile badges. Global oversight is maintained for System Administrators.
- **Pet Management Restriction:** Removed the "Add New Pet" option for Veterinarians and Staff. Only Pet Owners can now add new pets to the system.
- **AI Diagnosis UI Refinement:** Removed the "Book Appointment" button from the AI Diagnosis results page when viewed by a Veterinarian, as they do not need to book slots with themselves.
- **Profile UI Refinement:** Reorganized the profile page to show the picture on the left and information on the right. Replaced generic icons with actual user profile pictures in the navigation bar.
- **Layout Improvements:** Added a gap between the "VetWorkflow" brand and navigation links. Ensured the copyright footer stays at the bottom of every page.
- **Roles:** Removed the "Receptionist" role from the system as per requirements.
- **Navigation Menu:** Restricted "My Pets" visibility. It is now only visible to users with the `Pet Owner` role (`user.is_pet_owner`). This prevents Veterinarians and other staff from seeing the "My Pets" link in the main navigation bar.
