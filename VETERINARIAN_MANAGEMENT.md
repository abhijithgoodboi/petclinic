# Veterinarian Management Guide

## Overview

Starting from February 2026, veterinarians **cannot register through the public website**. All veterinarian accounts must be created by administrators through the Django Admin Panel.

This ensures better control and security over who can access veterinarian privileges.

---

## How to Create a Veterinarian Account

### Step 1: Access Django Admin Panel

1. Go to: http://127.0.0.1:8000/admin/
2. Log in with your admin credentials

### Step 2: Create the User Account

1. Click on **Users** under the "Accounts" section
2. Click the **Add User** button (top right)
3. Fill in the required fields:
   - **Username**: e.g., `dr.smith`
   - **Password**: Set a temporary password
4. Click **Save**

### Step 3: Edit the User

After creating the user, you'll be redirected to the edit page. Now set:

1. **First Name**: e.g., `John`
2. **Last Name**: e.g., `Smith`
3. **Email**: e.g., `dr.smith@pet-hospital.com`
4. **Role**: Select **Veterinarian** from the dropdown
5. **Phone Number**: Contact number
6. **Date of Birth**: Required field
7. **Save**

### Step 4: Create Veterinarian Profile

After saving the user, scroll down and click **Add** next to Veterinarian Profile:

1. **User**: Should auto-select the user you just created
2. **License Number**: e.g., `VET-2026-001` (unique)
3. **Specialization**: e.g., `Small Animal Medicine`
4. **Years of Experience**: e.g., `5`
5. **Qualifications**: e.g., `B.V.Sc, M.V.Sc`
6. **Consultation Fee**: e.g., `500.00`
7. **Bio**: Brief description (optional)
8. **Available for Emergency**: Check if they can handle emergencies
9. **Save**

---

## Quick Checklist

| Task | Location | Status |
|------|----------|--------|
| Create User account | Accounts > Users | [ ] |
| Set Role to Veterinarian | User edit page | [ ] |
| Create Veterinarian Profile | User edit page > Veterinarian Profile | [ ] |

---

## User Roles Reference

| Role | Registration | Description |
|------|--------------|-------------|
| **Pet Owner** | Public website | Can book appointments, register pets, use AI diagnosis |
| **Veterinarian** | Admin panel only | Can view appointments, create medical records, review AI diagnoses |
| **Administrator** | Admin panel only | Full system access, manage all users and settings |

---

## Frequently Asked Questions

### Can veterinarians register themselves?

**No.** Only pet owners can register through the website. Veterinarians must be created by an administrator.

### How do I change a pet owner's account to a veterinarian?

1. Go to **Accounts > Users**
2. Find the user
3. Click on the username
4. Change the **Role** dropdown to "Veterinarian"
5. **Save**
6. Then add a Veterinarian Profile for them

### How do I remove veterinarian access?

1. Go to **Accounts > Users**
2. Find the user
3. Click on the username
4. Change the **Role** dropdown to "Pet Owner"
5. **Save**
6. (Optional) Delete their Veterinarian Profile from the admin

### Can I create multiple veterinarians at once?

Yes, but you must create each user and profile individually through the admin panel.

### What if I need to delegate admin access?

To create another administrator:
1. Go to **Accounts > Users**
2. Click **Add User**
3. Fill in the details
4. After saving, check **Staff status** and **Superuser status**
5. Set Role to "Administrator"
6. Save

---

## Troubleshooting

### User shows as "Pet Owner" but needs to be "Veterinarian"

The role is set at the user level. Edit the user and change the Role dropdown.

### Veterinarian can't see appointments

Make sure the user has both:
1. User.role = 'VET'
2. A complete VeterinarianProfile linked to the user

### Cannot add Veterinarian Profile

The profile requires a unique license number. Make sure it's not already used by another veterinarian.

---

## Security Notes

- Keep admin credentials secure
- Only trusted personnel should have admin access
- Review veterinarian accounts periodically
- Change passwords regularly
