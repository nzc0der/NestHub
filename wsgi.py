# wsgi.py
# Production WSGI entry point for Gunicorn / UWSGI.
import os
import sys

# Ensure the project root is in the path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from server import create_app

app = create_app()
