@echo off
echo Starting VetCare Server...
call .\venv\Scripts\activate
python manage.py runserver
pause
