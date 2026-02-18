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
# DATABASE - SQLite for free tier (MySQL requires paid account)
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
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Create static directory if it doesn't exist
os.makedirs(STATIC_ROOT, exist_ok=True)

# ==============================================================================
# MEDIA FILES CONFIGURATION
# ==============================================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Create media directory if it doesn't exist
os.makedirs(MEDIA_ROOT, exist_ok=True)

# ==============================================================================
# CORS SETTINGS (if using django-cors-headers)
# ==============================================================================
# Only add these if you have 'corsheaders' in INSTALLED_APPS
if 'corsheaders' in INSTALLED_APPS:
    CORS_ALLOWED_ORIGINS = [
        'https://osozi.pythonanywhere.com',
        'http://osozi.pythonanywhere.com',
    ]
    CORS_ALLOW_CREDENTIALS = True

# ==============================================================================
# WHITENOISE CONFIGURATION (for static files)
# ==============================================================================
# Add whitenoise to middleware if installed
if 'whitenoise' in INSTALLED_APPS:
    # Insert after SecurityMiddleware or at position 1
    security_middleware = 'django.middleware.security.SecurityMiddleware'
    whitenoise_middleware = 'whitenoise.middleware.WhiteNoiseMiddleware'
    
    if security_middleware in MIDDLEWARE:
        idx = MIDDLEWARE.index(security_middleware) + 1
        MIDDLEWARE.insert(idx, whitenoise_middleware)
    else:
        MIDDLEWARE.insert(1, whitenoise_middleware)
    
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'NutriApp': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Create logs directory
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

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
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_filters.OrderingFilter',
    ],
}

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
# SECRET KEY (use environment variable in production)
# ==============================================================================
# Try to get SECRET_KEY from environment, otherwise use a default (not recommended for production)
import os
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    # For local testing only - in production, set this in PythonAnywhere env vars
    from django.core.management.utils import get_random_secret_key
    SECRET_KEY = get_random_secret_key()
    print("⚠️ WARNING: Using generated SECRET_KEY. Set DJANGO_SECRET_KEY environment variable for production!")

print(f"🚀 Running in PRODUCTION mode with SQLite database")
print(f"📁 Static files root: {STATIC_ROOT}")
print(f"📁 Media files root: {MEDIA_ROOT}")