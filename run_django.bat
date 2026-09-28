@echo off
echo ========================================================
echo Starting Liver Proteomics Aging Portal (Django + DRF)
echo ========================================================
cd /d "%~dp0liver_django"
python manage.py runserver 0.0.0.0:8000
pause
