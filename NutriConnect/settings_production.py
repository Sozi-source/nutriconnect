"""
Production settings for NutriConnect API on PythonAnywhere (Free Tier - SQLite)
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
# CRITICAL SECURITY SETTINGS
# ==============================================================================
DEBUG = False

ALLOWED_HOSTS = [
    'osozi.pythonanywhere.com',
    '127.0.0.1',
    'localhost',
    '.pythonanywhere.com',
]

# ==============================================================================
# CORS CONFIGURATION
# ==============================================================================

# Ensure corsheaders is in INSTALLED_APPS
if 'corsheaders' not in INSTALLED_APPS:
    INSTALLED_APPS.append('corsheaders')

# CORS middleware must be at the top
if 'corsheaders.middleware.CorsMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(0, 'corsheaders.middleware.CorsMiddleware')

# Allow your Next.js frontend domains
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000"
]

# Allow credentials (cookies, authorization headers)
CORS_ALLOW_CREDENTIALS = True

# Allow all necessary headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Allow all methods needed
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# CSRF trusted origins (for session authentication)
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
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
# DATABASE - SQLite for free tier
# ==============================================================================
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
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Add whitenoise for static files - ensure it's after CorsMiddleware
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# ==============================================================================
# MEDIA FILES CONFIGURATION
# ==============================================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/osozi/nutriconnect/media'

# ==============================================================================
# SECRET KEY - Improved with better error handling
# ==============================================================================
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    print("⚠️ WARNING: DJANGO_SECRET_KEY not set in environment variables!")
    print("⚠️ Using a generated key - this will cause session issues on restart!")
    from django.core.management.utils import get_random_secret_key
    SECRET_KEY = get_random_secret_key()
else:
    print("✅ DJANGO_SECRET_KEY loaded from environment")

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/home/osozi/nutriconnect/logs/django.log',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'corsheaders': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ==============================================================================
# Django REST Framework settings
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

print(f"🚀 Running in PRODUCTION mode with SQLite database")
print(f"🌐 CORS allowed origins: {CORS_ALLOWED_ORIGINS}")
print(f"🛡️ CSRF trusted origins: {CSRF_TRUSTED_ORIGINS}")
