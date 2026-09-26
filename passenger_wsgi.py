import sys
import os

# -----------------------------------------------------------------------------
# cPanel Passenger WSGI Entrypoint for Primexa Exchange (Python 3.13)
# -----------------------------------------------------------------------------

# Add project root directory to python path
sys.path.insert(0, os.path.dirname(__file__))

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primexa_project.settings")

# Import WSGI handler
from primexa_project.wsgi import application

