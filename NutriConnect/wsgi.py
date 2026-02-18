# Add your project directory to the Python path
import sys
import os

# This is your project path
path = '/home/osozi/nutriconnect'
if path not in sys.path:
    sys.path.append(path)

# Set the Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'nutriconnect.settings'

# Then the standard Django WSGI handler
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()