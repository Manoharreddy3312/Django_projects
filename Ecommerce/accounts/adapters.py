from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .models import UserProfile


class CustomAccountAdapter(DefaultAccountAdapter):
    pass


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not user.email and data.get('email'):
            user.email = data['email']
        user.is_email_verified = True
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        extra = sociallogin.account.extra_data
        name = extra.get('name') or ''
        picture = extra.get('picture')
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if name and not profile.full_name:
            profile.full_name = name
            profile.save(update_fields=['full_name'])
        if picture and not user.avatar:
            # Optional: download image — skipped to avoid network in sync request
            pass
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])
        return user
