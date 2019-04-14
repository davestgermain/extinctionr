#!/bin/sh

export PYTHONPATH=/home/src/extinctionr/

source /home/xr/venv/bin/activate

export DEBUG='false'
export DJANGO_SETTINGS_MODULE=extinctionr.prod_settings

python manage.py migrate
python manage.py collectstatic --noinput
exec gunicorn extinctionr.wsgi
