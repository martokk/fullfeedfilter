#!/bin/bash
# Entrypoint script for Dockerfile

poetry run python manage.py makemigrations --noinput
poetry run python manage.py migrate --noinput

if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
    python manage.py createsuperuser \
        --noinput \
        --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL
fi

poetry run ./manage.py runserver 0.0.0.0:8002
