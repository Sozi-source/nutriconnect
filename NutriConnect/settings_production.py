"""
Production settings for NutriConnect API on PythonAnywhere
"""

from .settings import *
import os

# ==============================================================================
# CRITICAL SECURITY SETTINGS
# ==============================================================================
DEBUG = False

# PythonAnywhere domain format: yourusername.pythonanywhere.com
ALLOWED_HOSTS = [
    'osozi.pythonanywhere.com',  # Replace with your username
    '127.0.0.1',
    'localhost',
]

# ==============================================================================
# SECURITY HEADERS
# ==============================================================================
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
# PythonAnywhere handles SSL, so SECURE_SSL_REDIRECT may not be needed
SECURE_SSL_REDIRECT = False  # PythonAnywhere provides HTTPS automatically
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# ==============================================================================
# DATABASE - MySQL (PythonAnywhere's free tier)
# ==============================================================================
# PythonAnywhere free tier uses MySQL
# You'll create this in the PythonAnywhere dashboard
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'osozi$nutriconnect',  # Format: username$dbname
        'USER': 'osozi',
        'PASSWORD': 'your-database-password',
        'HOST': 'osozi.mysql.pythonanywhere-services.com',
        'PORT': '',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ==============================================================================
# STATIC FILES
# ==============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = '/home/osozi/NutriConnect/staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==============================================================================
# MEDIA FILES
# ==============================================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/osozi/NutriConnect/media'

# ==============================================================================
# CORS SETTINGS
# ==============================================================================
CORS_ALLOWED_ORIGINS = [
    'https://osozi.pythonanywhere.com',
    'http://osozi.pythonanywhere.com',
]

# ==============================================================================
# LOGGING - Monitor on PythonAnywhere
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
            'filename': '/home/osozi/NutriConnect/logs/django.log',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}