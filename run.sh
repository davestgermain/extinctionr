#!/bin/sh

export DEBUG='false'

python3 manage.py migrate
python3 manage.py collectstatic
gunicorn extinctionr.wsgi