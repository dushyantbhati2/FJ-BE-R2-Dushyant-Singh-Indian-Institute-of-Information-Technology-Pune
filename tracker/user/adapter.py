from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
from user.models import Profile

User = get_user_model()

class MyAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        return resolve_url("/")

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        print("User created:", user)  # Debugging

        profile, created = Profile.objects.get_or_create(user=user, defaults={'balance': 100})
        print("Profile created:", created)  # Debugging

        return user