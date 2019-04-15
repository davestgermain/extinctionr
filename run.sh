#!/bin/bash

export PYTHONPATH=/home/src/extinctionr/

source /home/xr/venv/bin/activate

export DEBUG='false'
export DJANGO_SETTINGS_MODULE=extinctionr.prod_settings

python manage.py migrate --settings=extinctionr.prod_settings
python manage.py collectstatic --settings=extinctionr.prod_settings --noinput
exec gunicorn -w 2 --keep-alive 3600 extinctionr.wsgi
