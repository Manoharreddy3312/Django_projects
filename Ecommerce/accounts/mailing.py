from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_activation_email(user, token):
    link = f"{settings.SITE_URL.rstrip('/')}/accounts/activate/{token}/"
    body = render_to_string(
        'accounts/email/activation.txt',
        {'user': user, 'link': link},
    )
    send_mail(
        'Activate your FlipMart account',
        body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_password_reset_email(user, token):
    link = f"{settings.SITE_URL.rstrip('/')}/accounts/reset-password/{token}/"
    body = render_to_string(
        'accounts/email/password_reset.txt',
        {'user': user, 'link': link},
    )
    send_mail(
        'Reset your FlipMart password',
        body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
