#!/usr/bin/env bash
# Script de build usado na hospedagem em nuvem (Render).
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py popular_dados   # garante a lista básica de competências
