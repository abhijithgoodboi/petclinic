#!/bin/bash

echo "========================================="
echo "VetCare Platform Setup"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python 3.11 is installed
if ! command -v python3.11 &> /dev/null; then
    echo -e "${YELLOW}Python 3.11 is not found. Attempting to fallback to python3...${NC}"
    if ! command -v python3 &> /dev/null; then
        echo "Python is not installed. Please install Python 3.11."
        exit 1
    fi
    PYTHON_BIN="python3"
else
    echo -e "${GREEN}✓ Python 3.11 found${NC}"
    PYTHON_BIN="python3.11"
fi

# Create virtual environment
echo ""
echo "Creating virtual environment using ${PYTHON_BIN}..."
$PYTHON_BIN -m venv venv

echo -e "${GREEN}✓ Virtual environment created${NC}"

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install all dependencies from requirements.txt
echo ""
echo "Installing all dependencies (including OpenCV, TensorFlow, etc.)..."
pip install -r requirements.txt

echo -e "${GREEN}✓ All dependencies installed${NC}"

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p static
mkdir -p media
mkdir -p media/profiles
mkdir -p media/pets
mkdir -p media/medical_documents
mkdir -p media/ai_diagnosis/images
mkdir -p templates
mkdir -p ai_diagnosis/models

echo -e "${GREEN}✓ Directories created${NC}"

# Create .env file
echo ""
echo "Creating .env file..."
cat > .env << 'ENVEOF'
# Django settings
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database settings
# DB_NAME=vetcare_db
# DB_USER=your_username
# DB_PASSWORD=your_password

# Email settings
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@vetcare.com

# AI Settings
AI_MODEL_PATH=ai_diagnosis/models/skin_disease_model.h5
ENVEOF

echo -e "${GREEN}✓ .env file created${NC}"

# Run migrations
echo ""
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

echo -e "${GREEN}✓ Migrations completed${NC}"

# Create superuser
echo ""
echo -e "${YELLOW}Do you want to create a superuser now? (y/n)${NC}"
read -r create_superuser
if [ "$create_superuser" = "y" ]; then
    python manage.py createsuperuser
fi

# Collect static files
echo ""
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "========================================="
echo -e "${GREEN}Setup completed successfully!${NC}"
echo "========================================="
echo ""
echo "To start the development server:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run server: python manage.py runserver"
echo ""
echo "Access the application at: http://127.0.0.1:8000/"
echo "Access admin panel at: http://127.0.0.1:8000/admin/"
echo ""
