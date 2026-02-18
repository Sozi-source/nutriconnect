"""
Production settings for NutriConnect API on PythonAnywhere (Free Tier - SQLite)
"""

from .settings import *
import os

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
try:
    CORS_ALLOWED_ORIGINS = [
        'https://osozi.pythonanywhere.com',
        'http://osozi.pythonanywhere.com',
    ]
    CORS_ALLOW_CREDENTIALS = True
except NameError:
    # corsheaders not installed, skip
    pass

# ==============================================================================
# WHITENOISE CONFIGURATION (for static files)
# ==============================================================================
# Add whitenoise to middleware if installed
try:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
except NameError:
    # whitenoise not installed, skip
    pass

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
        'rest_framework.filters.OrderingFilter',
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
# You can keep the same key or use environment variable
# SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', SECRET_KEY)

print(f"🚀 Running in PRODUCTION mode with SQLite database")
print(f"📁 Static files root: {STATIC_ROOT}")
print(f"📁 Media files root: {MEDIA_ROOT}")