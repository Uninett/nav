from django.conf import settings

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.adapter import get_adapter as get_account_adapter
from allauth.mfa.adapter import DefaultMFAAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount import app_settings as socialaccount_app_settings


class NAVAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        """
        Whether to allow sign ups with username/password
        """
        allow_signups = super().is_open_for_signup(request)
        # Override with setting, otherwise default to super.
        return getattr(settings, "ACCOUNT_ALLOW_SIGNUPS", allow_signups)


class NAVSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        """
        Whether to allow sign ups via social account
        """
        if socialaccount_app_settings.AUTO_SIGNUP:
            return True
        return get_account_adapter(request).is_open_for_signup(request)


class NAVMFAAdapter(DefaultMFAAdapter):
    def is_mfa_enabled(self, user, types=None) -> bool:
        # NAV "enabled = no" -> MFA_SUPPORTED_TYPES = []
        # allauth's default is ["totp", "recovery_codes"]
        if getattr(settings, "MFA_SUPPORTED_TYPES", []) == []:
            types = []
        return super().is_mfa_enabled(user, types)
