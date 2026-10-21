#!/usr/bin/env bash
# Script de build usado na hospedagem em nuvem (Render).
# O plano gratuito não tem Shell, então tarefas de dados rodam aqui, controladas por variáveis de ambiente.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# DEMO_DATA=True cria usuários e projetos de exemplo (seguro rodar várias vezes).
if [ "${DEMO_DATA}" = "True" ]; then
  python manage.py popular_dados --demo
else
  python manage.py popular_dados
fi

# Cria o administrador se DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL e
# DJANGO_SUPERUSER_PASSWORD estiverem definidas (ignora se ele já existir).
if [ -n "${DJANGO_SUPERUSER_PASSWORD}" ]; then
  python manage.py createsuperuser --no-input 2>/dev/null || echo "Administrador já existe."
fi
