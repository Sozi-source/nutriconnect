# /var/www/osozi_pythonanywhere_com_wsgi.py
import os
import sys

# Add your project directory to the path
path = '/home/osozi/nutriconnect'
if path not in sys.path:
    sys.path.append(path)

# Set environment variable to use your production settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'NutriConnect.settings_production'

# For Python 3.9+ on PythonAnywhere, you don't need activate_this.py
# Just set the virtualenv path in the Web tab
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()