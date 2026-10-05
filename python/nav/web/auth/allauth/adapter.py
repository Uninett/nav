from django.conf import settings

from allauth.account import app_settings as account_settings
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_username
from allauth.mfa.adapter import DefaultMFAAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class NAVAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        """
        Whether to allow sign ups with username/password
        """
        allow_signups = super().is_open_for_signup(request)
        # Override with setting, otherwise default to super.
        return getattr(settings, "ACCOUNT_ALLOW_SIGNUPS", allow_signups)

    def populate_username(self, request, user):
        # NAV's login field is a VarcharField (TextField subclass) with no
        # max_length. allauth's default generate_unique_username crashes on a
        # None max_length. populate_user already sets user.login from the
        # social account uid, so just keep the existing username as-is.
        if account_settings.USER_MODEL_USERNAME_FIELD:
            username = user_username(user)
            if username:
                user_username(user, username)


class NAVSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        """Whether to provision a brand-new NAV account from a social identity.

        Disabled by default. Provisioning accounts from an external identity
        needs an authorization design (who may sign up, who becomes admin, and
        for which provider) that is not in place yet, so signup stays closed.

        Enable ``NAV_ALLOW_SIGNUPS`` to auto-provision accounts for first-time
        social logins instead of pre-creating each account manually -- only
        sound when the IdP itself controls who may reach NAV. It is a
        provisional, unsupported power-user escape hatch (set in
        ``local_settings``): a NAV-specific setting, not an allauth one,
        expected to be replaced by a single ``authentication.toml`` option once
        the authorization design lands. Existing users who have already
        connected a social account are unaffected; only first-time provisioning
        is gated.
        """
        return getattr(settings, "NAV_ALLOW_SIGNUPS", False)

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        # Ensure a username exists so populate_username does not fall through to
        # allauth's generate_unique_username, which crashes on NAV's login field
        # having no max_length. The uid is a minimal default identity; the
        # eventual signup design may map identity from a specific claim instead.
        if not getattr(user, "login", None):
            user.login = sociallogin.account.uid
        return user


class NAVMFAAdapter(DefaultMFAAdapter):
    def is_mfa_enabled(self, user, types=None) -> bool:
        # NAV "enabled = no" -> MFA_SUPPORTED_TYPES = []
        # allauth's default is ["totp", "recovery_codes"]
        if getattr(settings, "MFA_SUPPORTED_TYPES", []) == []:
            types = []
        return super().is_mfa_enabled(user, types)
