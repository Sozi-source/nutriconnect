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
]

# ==============================================================================
# SECURITY HEADERS
# ==============================================================================
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = False
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

INSTALLED_APPS += [
    'corsheaders',  # Add if not already present
]

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
# CORS middleware must be at the top
MIDDLEWARE.insert(0, 'corsheaders.middleware.CorsMiddleware')

# Allow your Next.js frontend domains
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",      # Next.js local development
    "http://localhost:3001",      # Alternative port
    "http://127.0.0.1:3000",
    "https://your-frontend.vercel.app",  # Replace with your actual frontend URL
    "https://your-custom-domain.com",     # If you have a custom domain
]

# If you need to allow credentials (cookies, authorization headers)
CORS_ALLOW_CREDENTIALS = True

# Allow all headers
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

# Allow all methods
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
    "https://your-frontend.vercel.app",
]

# If you're having CORS issues during development, you can temporarily use:
# CORS_ALLOW_ALL_ORIGINS = True  # Only for testing, NEVER in production!
# But for production, always use CORS_ALLOWED_ORIGINS

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
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    from django.core.management.utils import get_random_secret_key
    SECRET_KEY = get_random_secret_key()
    print("⚠️ WARNING: Using generated SECRET_KEY. Set DJANGO_SECRET_KEY environment variable!")

print(f"🚀 Running in PRODUCTION mode with SQLite database")
