import logging
from os.path import join

from nav.config import NAVConfigParser


__all__ = []
_logger = logging.getLogger(__name__)


# See https://docs.allauth.org/en/latest/mfa/index.html for more docs
class MFAConfigParser(NAVConfigParser):
    _KEY = "multi-factor-authentication"
    DEFAULT_CONFIG_FILES = [join('webfront', 'webfront.conf')]
    DEFAULT_CONFIG = f"""
[{_KEY}]
enabled=no
support-recovery-codes=yes
support_passkeys=no
support-passkey-signups=no
allow-insecure-origin=no
"""

    def is_mfa_enabled(self):
        return self.getboolean(self._KEY, 'enabled', fallback=False)

    def are_recovery_codes_enabled(self):
        return self.getboolean(self._KEY, 'support-recovery-codes', fallback=True)

    def are_passkeys_enabled(self):
        return self.getboolean(self._KEY, 'support-passkeys', fallback=False)

    def are_passkey_signups_enabled(self):
        return self.getboolean(self._KEY, 'support-passkey-signups', fallback=False)

    def are_insecure_origins_allowed(self):
        # Set to True when developing
        return self.getboolean(self._KEY, 'allow-insecure-origin', fallback=False)

    def get_MFA_SUPPORTED_TYPES_setting(self):
        methods = []
        if self.is_mfa_enabled():
            methods.append("totp")
            if self.are_recovery_codes_enabled():
                methods.append("recovery_codes")
            if self.are_passkeys_enabled():
                methods.append("passkeys")
        return methods

    def get_MFA_PASSKEY_LOGIN_ENABLED_setting(self):
        return self.is_mfa_enabled() and self.are_passkeys_enabled()

    def get_MFA_PASSKEY_SIGNUP_ENABLED_setting(self):
        return (
            self.get_MFA_PASSKEY_LOGIN_ENABLED_setting()
            and self.are_passkey_signups_enabled()
        )

    def get_MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN_setting(self):
        return (
            self.get_MFA_PASSKEY_LOGIN_ENABLED_setting()
            and self.are_insecure_origins_allowed()
        )

    def log_config(self):
        """Log MFA settings

        This should not happen during creation of Django settings,
        leads to noise.
        """
        methods = self.get_MFA_SUPPORTED_TYPES_setting(self) or None
        _logger.info("Supported MFA authentication methods: %s", methods)
        passkeys = self.get_MFA_PASSKEY_LOGIN_ENABLED_setting()
        _logger.info("Support login with passkeys (webauthn): %s", passkeys)
        if passkeys:
            _logger.info(
                "Support signups with passkeys (webauthn): %s",
                self.get_MFA_PASSKEY_SIGNUP_ENABLED_setting(),
            )
            insecure_message = "Support insecure origin for passkeys"
            if self.get_MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN_setting():
                _logger.warn(f"{insecure_message}: yes, this is a security risk!")
            else:
                _logger.info(f"{insecure_message}: no")
