"""
Production settings for NutriConnect API on PythonAnywhere (Free Tier - SQLite)
"""

from .settings import *
import os
from pathlib import Path

# ==============================================================================
# BASE DIRECTORY
# ==============================================================================
# Define BASE_DIR if not already defined in settings.py
try:
    BASE_DIR
except NameError:
    BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# CRITICAL SECURITY SETTINGS
# ==============================================================================
DEBUG = False

# PythonAnywhere domain
ALLOWED_HOSTS = [
    'osozi.pythonanywhere.com',
    '127.0.0.1',
    'localhost',
]

# ==============================================================================
# SECURITY HEADERS
# ==============================================================================
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = False  # PythonAnywhere provides HTTPS automatically
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# ==============================================================================
# DATABASE - FORCE SQLite for free tier
# ==============================================================================
# Override any existing database configuration to use SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==============================================================================
# STATIC FILES CONFIGURATION
# ==============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = '/home/osozi/nutriconnect/staticfiles'

# ==============================================================================
# MEDIA FILES CONFIGURATION
# ==============================================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/osozi/nutriconnect/media'

# ==============================================================================
# SECRET KEY
# ==============================================================================
# Use environment variable or generate one
import os
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    from django.core.management.utils import get_random_secret_key
    SECRET_KEY = get_random_secret_key()
    print("⚠️ WARNING: Using generated SECRET_KEY. Set DJANGO_SECRET_KEY environment variable for production!")

print(f"🚀 Running in PRODUCTION mode with SQLite database")
print(f"📁 Database path: {DATABASES['default']['NAME']}")