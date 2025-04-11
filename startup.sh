#!/bin/bash
pip install -r requirements.txt
exec gunicorn -b 0.0.0.0:8000 app:app
