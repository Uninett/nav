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

    def populate_username(self, request, user):
        # NAV's login field is a VarcharField (TextField subclass) with no max_length.
        # allauth's default generate_unique_username crashes on None max_length.
        # populate_user already sets user.login from the social account uid.
        from allauth.account import app_settings as account_settings
        from allauth.account.utils import user_username

        if account_settings.USER_MODEL_USERNAME_FIELD:
            username = user_username(user)
            if username:
                user_username(user, username)


class NAVSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        """
        Whether to allow sign ups via social account
        """
        if socialaccount_app_settings.AUTO_SIGNUP:
            return True
        return get_account_adapter(request).is_open_for_signup(request)

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not getattr(user, 'login', None):
            user.login = sociallogin.account.uid
        return user

    def pre_social_login(self, request, sociallogin):
        """Connect OIDC login to existing NAV account by uid before signup runs."""
        from nav.models.profiles import Account

        if sociallogin.is_existing:
            return
        uid = sociallogin.account.uid
        if not uid:
            return
        try:
            existing = Account.objects.get(login=uid)
            sociallogin.connect(request, existing)
        except Account.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        extra = sociallogin.account.extra_data
        token = extra.get('id_token', extra)
        userinfo = extra.get('userinfo', token)
        user = sociallogin.user
        user.login = sociallogin.account.uid
        user.name = userinfo.get('name') or token.get('name', '')
        user.ext_sync = 'oidc'
        return super().save_user(request, sociallogin, form)


class NAVMFAAdapter(DefaultMFAAdapter):
    def is_mfa_enabled(self, user, types=None) -> bool:
        # NAV "enabled = no" -> MFA_SUPPORTED_TYPES = []
        # allauth's default is ["totp", "recovery_codes"]
        if getattr(settings, "MFA_SUPPORTED_TYPES", []) == []:
            types = []
        return super().is_mfa_enabled(user, types)
