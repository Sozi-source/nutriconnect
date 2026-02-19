"""
Local development settings for NutriConnect
"""

from .settings import *
import os
from pathlib import Path

# ==============================================================================
# BASE DIRECTORY
# ==============================================================================
try:
    BASE_DIR
except NameError:
    BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# DEVELOPMENT SETTINGS - DEBUG ON
# ==============================================================================
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# ==============================================================================
# DATABASE - SQLite for local development
# ==============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==============================================================================
# CORS SETTINGS - Allow local Next.js
# ==============================================================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

# ==============================================================================
# DJANGO REST FRAMEWORK SETTINGS
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ==============================================================================
# STATIC AND MEDIA FILES
# ==============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ==============================================================================
# CUSTOM USER MODEL
# ==============================================================================
AUTH_USER_MODEL = 'NutriApp.User'

# ==============================================================================
# TIME ZONE
# ==============================================================================
TIME_ZONE = 'Africa/Nairobi'
USE_TZ = True

# ==============================================================================
# SECRET KEY - Use a fixed key for development
# ==============================================================================
SECRET_KEY = 'django-insecure-development-key-12345'

# Create directories
os.makedirs(STATIC_ROOT, exist_ok=True)
os.makedirs(MEDIA_ROOT, exist_ok=True)

print("🚀 Running in LOCAL development mode")
print(f"📁 Database: {DATABASES['default']['NAME']}")