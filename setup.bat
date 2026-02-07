@echo off
echo =========================================
echo VetCare Platform - Windows Setup
echo =========================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python 3.11 from python.org
    pause
    exit /b
)

:: Create Virtual Environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b
)

:: Activate Virtual Environment and Install Dependencies
echo.
echo Installing dependencies...
call .\venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

:: Create necessary directories
echo.
echo Creating directories...
if not exist "static" mkdir static
if not exist "media" mkdir media
if not exist "media\profiles" mkdir media\profiles
if not exist "media\pets" mkdir media\pets
if not exist "media\medical_documents" mkdir media\medical_documents
if not exist "media\ai_diagnosis\images" mkdir media\ai_diagnosis\images
if not exist "ai_diagnosis\models" mkdir ai_diagnosis\models

:: Create .env file
echo.
echo Creating .env file...
if not exist ".env" (
    echo SECRET_KEY=django-insecure-windows-dev-key > .env
    echo DEBUG=True >> .env
    echo ALLOWED_HOSTS=127.0.0.1,localhost >> .env
    echo EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend >> .env
    echo DEFAULT_FROM_EMAIL=noreply@vetcare.com >> .env
    echo AI_MODEL_PATH=ai_diagnosis/models/skin_disease_model.h5 >> .env
)

:: Run Migrations
echo.
echo Running database migrations...
python manage.py makemigrations
python manage.py migrate

:: Create Superuser Prompt
echo.
echo =========================================
echo Setup completed successfully!
echo =========================================
echo.
echo To start the server:
echo 1. call venv\Scripts\activate
echo 2. python manage.py runserver
echo.
pause
