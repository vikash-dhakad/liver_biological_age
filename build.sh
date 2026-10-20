#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "=========================================="
echo "Installing Python Dependencies..."
echo "=========================================="
pip install --upgrade pip
pip install -r requirements.txt

echo "=========================================="
echo "Running Django Migrations..."
echo "=========================================="
cd liver_django
python manage.py makemigrations --no-input
python manage.py migrate --no-input

echo "=========================================="
echo "Collecting Static Files..."
echo "=========================================="
python manage.py collectstatic --no-input

echo "=========================================="
echo "Build Completed Successfully!"
echo "=========================================="
