#!/bin/bash

export PYTHONPATH=/home/src/extinctionr/

source /home/xr/xrboston.org/venv/bin/activate

export DEBUG='false'
export DJANGO_SETTINGS_MODULE=extinctionr.prod_settings

python manage.py migrate --settings=extinctionr.prod_settings
python manage.py collectstatic --settings=extinctionr.prod_settings --noinput
python manage.py compress --force
exec gunicorn --threads 4 --max-requests 1000 --keep-alive 3600 extinctionr.wsgi
