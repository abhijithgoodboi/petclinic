# 🔐 Login & Registration Guide

## ✅ Fixed and Working!

Both login and registration are now fully functional.

## 🚀 How to Test

### Start the Server
```bash
cd ~/gits/veterinary_platform
python manage.py runserver
```

## 1️⃣ Login (Existing Users)

### URL: http://127.0.0.1:8000/accounts/login/

### Demo Account:
- **Username:** admin
- **Password:** admin123
- **Role:** Administrator

### Steps:
1. Go to http://127.0.0.1:8000/accounts/login/
2. Enter username: `admin`
3. Enter password: `admin123`
4. Click "Login"
5. You'll be redirected to the home page

## 2️⃣ Register (New Users)

### URL: http://127.0.0.1:8000/accounts/register/

### Registration Process:

1. **Go to Registration Page**
   - Navigate to http://127.0.0.1:8000/accounts/register/
   - Or click "Register" link on login page

2. **Fill in Required Fields:**
   - Username (unique)
   - Email (unique)
   - First Name
   - Last Name
   - Password (min 8 characters)
   - Confirm Password
   - Role (Pet Owner, Veterinarian, or Receptionist)

3. **Optional Fields:**
   - Phone Number
   - Address

4. **Submit**
   - Click "Register" button
   - You'll be automatically logged in
   - Redirected to home page

### Example Registration:

```
Username:       john_doe
Email:          john@example.com
First Name:     John
Last Name:      Doe
Password:       mypassword123
Confirm Pass:   mypassword123
Role:           Pet Owner
Phone:          +1234567890
Address:        123 Main St, City
```

## 3️⃣ User Roles

### Pet Owner
- Can add pets
- Book appointments
- View medical records
- Use AI diagnosis
- Track vaccinations

### Veterinarian
- Set availability
- View appointments
- Create medical records
- Write prescriptions
- Review AI diagnoses
- Handle emergencies

### Receptionist
- Book appointments for clients
- Manage schedules
- Handle emergency intake

### Administrator (via Django Admin)
- Full system access
- User management
- System configuration

## 4️⃣ After Login

### Pet Owner Dashboard Shows:
- My Pets
- Book Appointment
- My Appointments
- AI Diagnosis

### Veterinarian Dashboard Shows:
- Appointments
- Set Availability
- Emergency Cases
- AI Diagnoses

## 5️⃣ Profile Management

### View Profile
- URL: http://127.0.0.1:8000/accounts/profile/
- See your account details
- View your role and information

### Edit Profile
- Click "Edit Profile" button
- Update your information
- Save changes

## 6️⃣ Navigation

### Main Navigation Bar:
- **Home** - Dashboard
- **Appointments** - View/book appointments
- **My Pets** - Manage pets (Pet Owners)
- **AI Diagnosis** - Upload images for analysis
- **Emergency** - Emergency cases (Veterinarians)
- **Profile** - View/edit profile
- **Logout** - Sign out

## 🐛 Common Issues & Solutions

### Issue: "Username already exists"
**Solution:** Choose a different username

### Issue: "Email already registered"
**Solution:** Use a different email or login instead

### Issue: "Passwords do not match"
**Solution:** Make sure both password fields match exactly

### Issue: Can't see admin panel
**Solution:** Only admin users can access /admin/
- Regular users should use the main website
- To create admin: `python manage.py createsuperuser`

### Issue: Forgot password
**Solution:** Contact admin or reset via Django admin

## 📝 Test Accounts You Can Create

### Test Pet Owner:
```
Username: pet_owner1
Email: owner@test.com
Name: Sarah Johnson
Role: Pet Owner
Password: testpass123
```

### Test Veterinarian:
```
Username: dr_smith
Email: drsmith@test.com
Name: Dr. John Smith
Role: Veterinarian
Password: testpass123
```

### Test Receptionist:
```
Username: reception1
Email: reception@test.com
Name: Emily Brown
Role: Receptionist
Password: testpass123
```

## ✨ Features After Login

### For Pet Owners:
1. Add your pets
2. Book appointments
3. Upload images for AI diagnosis
4. View medical history
5. Track vaccinations

### For Veterinarians:
1. Set your availability
2. View assigned appointments
3. Create medical records
4. Handle emergency cases
5. Review AI predictions

## 🔒 Security Features

✅ Password hashing (secure storage)
✅ CSRF protection
✅ Session management
✅ Role-based access control
✅ Email uniqueness validation
✅ Username uniqueness validation

## 📱 Mobile Friendly

The login and registration pages are responsive and work on:
- Desktop browsers
- Tablets
- Mobile phones

## 🎯 Quick Links

- **Home:** http://127.0.0.1:8000/
- **Login:** http://127.0.0.1:8000/accounts/login/
- **Register:** http://127.0.0.1:8000/accounts/register/
- **Profile:** http://127.0.0.1:8000/accounts/profile/
- **Admin:** http://127.0.0.1:8000/admin/

---

## ✅ Verification Checklist

Test these to confirm everything works:

- [ ] Can access login page
- [ ] Can login with admin/admin123
- [ ] Can access registration page
- [ ] Can create new pet owner account
- [ ] Can create new veterinarian account
- [ ] Auto-redirected after successful registration
- [ ] Can view profile page
- [ ] Can edit profile
- [ ] Can logout
- [ ] Can login again after logout
- [ ] Role-specific dashboard shows correct options

---

**All login and registration features are working!** 🎉
