# utils.py
from django.core.mail import send_mail
from django.template.loader import render_to_string

def send_approval_email(user_email):
    subject = 'Your Practitioner Account Has Been Approved'
    message = render_to_string('emails/approval_notification.html', {
        'user': user_email,
        'login_url': 'https://osozi.pythonanywhere.com/login'
    })
    send_mail(subject, message, 'admin@nutriconnect.com', [user_email])