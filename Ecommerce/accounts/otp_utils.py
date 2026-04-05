import random
import re
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from .models import OTPChallenge, User


def _channel_value(channel):
    return channel.value if hasattr(channel, 'value') else str(channel)


def _rate_key(identifier, channel):
    return f'otp_rate:{_channel_value(channel)}:{identifier}'


def check_rate_limit(identifier, channel):
    """Returns (allowed: bool, retry_after_seconds: int)."""
    window = getattr(settings, 'OTP_WINDOW_SECONDS', 900)
    max_n = getattr(settings, 'OTP_MAX_PER_WINDOW', 5)
    key = _rate_key(identifier, channel)
    n = cache.get(key, 0)
    if n >= max_n:
        return False, window
    return True, 0


def bump_rate_limit(identifier, channel):
    window = getattr(settings, 'OTP_WINDOW_SECONDS', 900)
    max_n = getattr(settings, 'OTP_MAX_PER_WINDOW', 5)
    key = _rate_key(identifier, channel)
    try:
        n = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=window)
        n = 1
    return n <= max_n


def cooldown_ok(identifier, channel):
    """Minimum seconds between sends."""
    sec = getattr(settings, 'OTP_RATE_LIMIT_SECONDS', 60)
    key = f'otp_cool:{_channel_value(channel)}:{identifier}'
    if cache.get(key):
        return False
    cache.set(key, 1, timeout=sec)
    return True


def generate_code():
    return f'{random.randint(0, 999999):06d}'


def is_email(s):
    return '@' in s and re.match(r'^[^@]+@[^@]+\.[^@]+$', s.strip())


def is_phone(s):
    digits = re.sub(r'\D', '', s)
    return len(digits) >= 10


def normalize_identifier(raw):
    raw = raw.strip()
    if is_email(raw):
        return raw.lower(), OTPChallenge.Channel.EMAIL
    digits = re.sub(r'\D', '', raw)
    if len(digits) >= 10:
        return digits[-10:], OTPChallenge.Channel.SMS
    return None, None


def send_otp_email(email, code):
    from django.core.mail import send_mail

    send_mail(
        'Your FlipMart login code',
        f'Your OTP is {code}. It expires in {settings.OTP_EXPIRE_MINUTES} minutes.',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def send_otp_sms(phone, code):
    from django.conf import settings as dj_settings

    sid = dj_settings.TWILIO_ACCOUNT_SID
    token = dj_settings.TWILIO_AUTH_TOKEN
    from_num = dj_settings.TWILIO_PHONE_NUMBER
    if not (sid and token and from_num):
        raise RuntimeError('Twilio is not configured; use email OTP or set Twilio env vars.')
    from twilio.rest import Client

    client = Client(sid, token)
    client.messages.create(
        body=f'FlipMart OTP: {code}. Valid {dj_settings.OTP_EXPIRE_MINUTES} min.',
        from_=from_num,
        to=f'+91{phone}' if len(phone) == 10 else phone,
    )


def create_otp_challenge(identifier, channel):
    cv = _channel_value(channel)
    OTPChallenge.objects.filter(identifier=identifier, channel=cv).delete()
    code = generate_code()
    minutes = getattr(settings, 'OTP_EXPIRE_MINUTES', 5)
    expires = timezone.now() + timedelta(minutes=minutes)
    ch = OTPChallenge.objects.create(
        identifier=identifier,
        channel=cv,
        code_hash=make_password(code),
        expires_at=expires,
    )
    return ch, code


def verify_otp(identifier, channel, code):
    cv = _channel_value(channel)
    try:
        ch = OTPChallenge.objects.filter(identifier=identifier, channel=cv).latest('created_at')
    except OTPChallenge.DoesNotExist:
        return False, 'No OTP request found.'
    if ch.is_expired:
        return False, 'OTP expired.'
    if ch.attempts >= 5:
        return False, 'Too many attempts.'
    ch.attempts += 1
    ch.save(update_fields=['attempts'])
    if not check_password(code, ch.code_hash):
        return False, 'Invalid OTP.'
    ch.delete()
    return True, None


def get_or_create_user_for_otp(identifier, channel):
    if channel == OTPChallenge.Channel.EMAIL:
        user, created = User.objects.get_or_create(
            email=identifier.lower(),
            defaults={'is_email_verified': True, 'is_active': True},
        )
        if not created:
            user.is_email_verified = True
            user.is_active = True
            user.save(update_fields=['is_email_verified', 'is_active'])
        return user, created
    # phone
    phone = identifier
    user = User.objects.filter(phone=phone).first()
    if user:
        return user, False
    email = f'{phone}@phone.flipmart.local'
    user = User.objects.create_user(email=email, password=None)
    user.phone = phone
    user.is_active = True
    user.is_email_verified = False
    user.save()
    return user, True
