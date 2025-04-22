from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialApp
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
from django.shortcuts import resolve_url
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)


class CougarIDSocialAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        logger.error("👀 Pre-login account data: %s", sociallogin.account.extra_data)

    def is_open_for_signup(self, request, sociallogin):
        try:
            extra_data = sociallogin.account.extra_data
            logger.debug("🧪 FULL extra_data: %s", extra_data)

            email = (
                extra_data.get("email")
                or extra_data.get("preferred_username")
                or extra_data.get("mail")
                or extra_data.get("userPrincipalName")
                or ""
            ).lower()

            logger.debug("🧪 FINAL email used: %s", email)

            if email.endswith("@uh.edu") or email.endswith("@cougarnet.uh.edu"):
                return True

            raise ValidationError("Only CougarNet or UH accounts are allowed.")

        except Exception as e:
            logger.exception("🔥 ERROR in is_open_for_signup")
            raise ValidationError("Something went wrong while validating your login.")

    def get_login_redirect_url(self, request):
        user = request.user
        if user.is_superuser:
            return resolve_url("/admin/")
        elif hasattr(user, "role") and user.role == "approver":
            return resolve_url("/approvals/")
        return resolve_url("/dashboard/")


    def get_app(self, request, provider, client_id=None):
        try:
            return SocialApp.objects.get(provider=provider, sites__id=settings.SITE_ID)
        except MultipleObjectsReturned:
            apps = SocialApp.objects.filter(provider=provider, sites__id=settings.SITE_ID)
            return apps.first()
        except ObjectDoesNotExist:
            return None
