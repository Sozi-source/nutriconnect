#!/bin/bash
echo "🚀 Deploying NutriConnect..."
cd ~/nutriconnect
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
touch /var/www/osozi_pythonanywhere_com_wsgi.py
echo "✅ Deployment complete!"
