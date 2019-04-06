#!/bin/sh

export DEBUG='false'

python3.7 manage.py migrate
python3.7 manage.py collectstatic --noinput
exec gunicorn extinctionr.wsgi