#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Installing Python Dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Running Django Migrations..."
cd liver_django
python manage.py makemigrations --no-input
python manage.py migrate --no-input

echo "Collecting Static Files..."
python manage.py collectstatic --no-input

echo "Render Build Complete!"
