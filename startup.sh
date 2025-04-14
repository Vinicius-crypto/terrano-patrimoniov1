#!/bin/bash

export FLASK_APP=app.py
export FLASK_ENV=production

python3 -m pip install -r requirements.txt

exec gunicorn --bind=0.0.0.0:8000 app:app
