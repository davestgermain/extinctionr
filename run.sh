#!/bin/sh

export DEBUG='false'
export DJANGO_SETTINGS_MODULE=extinctionr.prod_settings

python3.7 manage.py migrate
python3.7 manage.py collectstatic --noinput
exec gunicorn extinctionr.wsgi