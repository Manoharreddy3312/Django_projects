from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import EmailActivationToken, OTPChallenge, PasswordResetToken, User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'phone', 'is_email_verified', 'is_staff', 'is_active')
    search_fields = ('email', 'phone')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_email_verified')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('phone', 'avatar', 'is_email_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2')}),
    )
    filter_horizontal = ('groups', 'user_permissions')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'country')
    search_fields = ('user__email', 'full_name')


admin.site.register(EmailActivationToken)
admin.site.register(PasswordResetToken)
admin.site.register(OTPChallenge)
