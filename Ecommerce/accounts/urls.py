from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('accounts/register/', views.RegisterView.as_view(), name='register'),
    path('accounts/login/', views.AccountLoginView.as_view(), name='login'),
    path('accounts/logout/', views.AccountLogoutView.as_view(), name='logout'),
    path('accounts/activate/<str:token>/', views.activate, name='activate'),
    path('accounts/password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('accounts/reset-password/<str:token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/profile/', views.ProfileView.as_view(), name='profile'),
    path('accounts/api/otp/request/', views.otp_request_view, name='otp_request'),
    path('accounts/api/otp/verify/', views.otp_verify_view, name='otp_verify'),
]
