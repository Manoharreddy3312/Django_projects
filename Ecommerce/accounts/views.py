import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView, UpdateView

from .forms import (
    EmailLoginForm,
    PasswordResetRequestForm,
    RegisterForm,
    SetNewPasswordForm,
    UserProfileForm,
)
from .mailing import send_activation_email, send_password_reset_email
from .models import EmailActivationToken, PasswordResetToken, User, UserProfile
from .otp_utils import (
    bump_rate_limit,
    check_rate_limit,
    cooldown_ok,
    create_otp_challenge,
    get_or_create_user_for_otp,
    normalize_identifier,
    send_otp_email,
    send_otp_sms,
    verify_otp,
)


class RegisterView(FormView):
    template_name = 'accounts/register.html'
    form_class = RegisterForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('store:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        tok = EmailActivationToken.create_for_user(user)
        try:
            send_activation_email(user, tok.token)
            messages.success(self.request, 'Check your email to activate your account.')
        except Exception:
            messages.warning(
                self.request,
                'Account created but email could not be sent. Contact support or use console backend in DEBUG.',
            )
        return redirect('accounts:login')


class AccountLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = EmailLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        nxt = self.request.GET.get('next') or self.request.POST.get('next')
        if nxt:
            return nxt
        return super().get_success_url()

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_active:
            messages.error(self.request, 'Please verify your email before logging in.')
            return self.form_invalid(form)
        if not user.is_email_verified and not user.socialaccount_set.exists():
            messages.error(self.request, 'Please verify your email before logging in.')
            return self.form_invalid(form)
        return super().form_valid(form)


class AccountLogoutView(LogoutView):
    next_page = '/'


def activate(request, token):
    tok = get_object_or_404(EmailActivationToken, token=token)
    user = tok.user
    user.is_active = True
    user.is_email_verified = True
    user.save(update_fields=['is_active', 'is_email_verified'])
    tok.delete()
    messages.success(request, 'Your account is active. You can log in.')
    return redirect('accounts:login')


class PasswordResetRequestView(FormView):
    template_name = 'accounts/password_reset_request.html'
    form_class = PasswordResetRequestForm

    def form_valid(self, form):
        email = form.cleaned_data['email'].strip().lower()
        user = User.objects.filter(email=email).first()
        if user:
            t = PasswordResetToken.create_for_user(user)
            try:
                send_password_reset_email(user, t.token)
            except Exception:
                messages.warning(self.request, 'Could not send email.')
        messages.success(
            self.request,
            'If an account exists for that email, you will receive reset instructions.',
        )
        return redirect('accounts:login')


class PasswordResetConfirmView(FormView):
    template_name = 'accounts/password_reset_confirm.html'
    form_class = SetNewPasswordForm

    def dispatch(self, request, *args, **kwargs):
        self.token_obj = get_object_or_404(PasswordResetToken, token=kwargs['token'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        u = self.token_obj.user
        u.set_password(form.cleaned_data['password1'])
        u.save()
        self.token_obj.delete()
        messages.success(self.request, 'Password updated. Log in with your new password.')
        return redirect('accounts:login')


class ProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'

    def get_object(self, queryset=None):
        return self.request.user.profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile saved.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('accounts:profile')


@require_http_methods(['POST'])
def otp_request_view(request):
    try:
        body = json.loads(request.body.decode()) if request.body else {}
    except json.JSONDecodeError:
        body = {}
    raw = body.get('identifier', '').strip()
    ident, channel = normalize_identifier(raw)
    if not ident:
        return JsonResponse({'ok': False, 'error': 'Enter a valid email or mobile number.'}, status=400)
    ok, retry = check_rate_limit(ident, channel)
    if not ok:
        return JsonResponse(
            {'ok': False, 'error': f'Too many OTP requests. Try again in {retry} seconds.'},
            status=429,
        )
    if not cooldown_ok(ident, channel):
        return JsonResponse({'ok': False, 'error': 'Please wait before requesting another OTP.'}, status=429)
    from .models import OTPChallenge

    ch, code = create_otp_challenge(ident, channel)
    try:
        if channel == OTPChallenge.Channel.EMAIL:
            send_otp_email(ident, code)
        else:
            send_otp_sms(ident, code)
    except Exception as e:
        ch.delete()
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)
    if not bump_rate_limit(ident, channel):
        pass
    return JsonResponse({'ok': True, 'message': 'OTP sent.'})


@require_http_methods(['POST'])
def otp_verify_view(request):
    try:
        body = json.loads(request.body.decode()) if request.body else {}
    except json.JSONDecodeError:
        body = {}
    raw = body.get('identifier', '').strip()
    code = ''.join(body.get('code', '').split())
    ident, channel = normalize_identifier(raw)
    if not ident or len(code) < 4:
        return JsonResponse({'ok': False, 'error': 'Invalid input.'}, status=400)
    ok, err = verify_otp(ident, channel, code)
    if not ok:
        return JsonResponse({'ok': False, 'error': err}, status=400)
    user, _ = get_or_create_user_for_otp(ident, channel)
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    nxt = body.get('next') or request.GET.get('next') or '/'
    return JsonResponse({'ok': True, 'redirect': nxt})

