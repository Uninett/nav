import logging

from nav.config.toml import TOMLConfigParser


_logger = logging.getLogger(__name__)


# See https://docs.allauth.org/en/latest/mfa/index.html for more docs
class MFAConfigParser(TOMLConfigParser):
    """Parse the "multi-factor-authentication" section of authentication.toml"""

    SECTION = "multi-factor-authentication"
    DEFAULT_CONFIG_FILE = "webfront/authentication.toml"
    DEFAULT_CONFIG = {
        SECTION: {
            "enabled": False,
            "support-recovery-codes": True,
            "support-passkeys": False,
            "support-passkey-signups": False,
            "allow-insecure-origin": False,
        }
    }

    def is_mfa_enabled(self):
        return self["enabled"]

    def are_recovery_codes_enabled(self):
        return self["support-recovery-codes"]

    def are_passkeys_enabled(self):
        return self["support-passkeys"]

    def are_passkey_signups_enabled(self):
        return self["support-passkey-signups"]

    def are_insecure_origins_allowed(self):
        # Set to True when developing
        return self["allow-insecure-origin"]

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


class SocialProviderHelper:
    """Helper class for social account configs

    Social account configs have a section inside a section structure that is
    a list of providers*, allowing for configs that hold for all providers on
    the SECTION.

    [*] Aka. idps for OIDC
    """

    _subkey: str

    def get_providers(self) -> dict:
        return self.get(self._subkey, {})

    def get_provider_config(self, provider: str) -> dict:
        providers = self.get_providers()
        return providers.get(provider, {})

    def _get_common_SOCIALACCOUNT_PROVIDERS_fields_for_provider(
        self, provider_config: dict
    ) -> dict:
        # Do not alter the provider_config below
        config = {}
        settings = provider_config.get("settings", {})
        config["client_id"] = provider_config["client_id"]
        config["secret"] = provider_config["secret"]
        if settings:
            config["settings"] = settings
        return config


class SocialConfigParser(SocialProviderHelper, TOMLConfigParser):
    """Parse the "social" section of authentication.toml

    Example:

    [social.providers.github]
    module-path = allauth.socialaccount.providers.github
    client_id = "not.optional"
    secret = "not.optional"
    scope = ["user:email"]  # optional, "user" scope is default for github
                            # and includes "user:email"
    """

    _subkey = "providers"
    SECTION = "social"
    DEFAULT_CONFIG_FILE = "webfront/authentication.toml"
    DEFAULT_CONFIG = {
        SECTION: {},
    }

    def translate_entry_for_provider(self, provider: str):
        provider_config = self.get_provider_config(provider)
        if not provider_config:
            return {}
        # Do not alter the provider_config below
        config = {}
        SCOPE = provider_config.get("scope", [])
        if SCOPE:
            config["SCOPE"] = SCOPE

        APP = self._get_common_SOCIALACCOUNT_PROVIDERS_fields_for_provider(
            provider_config
        )
        config["APP"] = APP
        return config

    def translate_all_provider_configs(self):
        configs = {}
        for provider in self.get_providers().keys():
            configs[provider] = self.translate_entry_for_provider(provider)
        return configs

    def generate_SOCIALACCOUNT_PROVIDERS(self):
        configs = self.translate_all_provider_configs()
        return configs

    def get_provider_import_paths(self):
        module_paths = []
        missing_modules = []
        for provider_id, provider_config in self.get_providers().values():
            if "module-path" in provider_config:
                module_paths.append(provider_config["module_path"])
            else:
                missing_modules.append(provider_id)
        if missing_modules:
            _logger.error(
                "No module path configured for social account provider(s) %s",
                ', '.join(missing_modules),
            )
        return module_paths


class OIDCConfigParser(SocialProviderHelper, TOMLConfigParser):
    """Parse the "oidc" section of authentication.toml

    Example:

    [oidc]
    module-path = "allauth.socialccount.providers.openid_connect"  # optional

    [oidc.idps.dataporten]
    provider = dataporten-oidc"  # The name after the dot is used in the URLs
    name = "Feide OIDC"  # Shown in login screen
    client_id = "not.optional"
    secret = "not.optional"
    server_url = "https://auth.dataporten.no/"  # NEVER optional
    Feide OIDC does not support the standard OIDC scopes/claims
    scope = ["userid-feide"]  # Other idps have "profile" for this

    [oidc.dataporten-oidc.settings]
    uid_field = "https://n.feide.no/claims/eduPersonPrincipalName"
    """

    _subkey = "idps"
    _module_path = "allauth.socialaccount.providers.openid_connect"
    SECTION = "oidc"
    DEFAULT_CONFIG_FILE = "webfront/authentication.toml"
    DEFAULT_CONFIG = {
        SECTION: {},
    }

    def translate_entry_for_provider(self, provider: str) -> dict:
        provider_config = self.get_provider_config(provider)
        if not provider_config:
            return {}
        APP = self._get_common_SOCIALACCOUNT_PROVIDERS_fields_for_provider(
            provider_config
        )
        APP["provider_id"] = provider
        APP["name"] = provider_config["name"]
        APP.setdefault("settings", {})
        try:
            APP["settings"]["server_url"] = provider_config["server_url"]
        except KeyError:
            raise KeyError('"server_url" is a mandatory setting')
        provider_settings = provider_config.get("settings", {})
        APP["settings"]["uid_field"] = provider_settings.get(
            "uid_field",
            "sub",
        )
        return APP

    def translate_all_provider_configs(self):
        configs = []
        for provider in self.get_providers().keys():
            configs.append(self.translate_entry_for_provider(provider))
        return configs

    def get_OAUTH_PKCE_ENABLED(self):
        return self.get("oauth_pkce_enabled", False)

    def generate_SOCIALACCOUNT_PROVIDERS(self) -> dict:
        configs = self.translate_all_provider_configs()
        if configs:
            return {
                "openid_connect": {
                    "OAUTH_PKCE_ENABLED": self.get_OAUTH_PKCE_ENABLED(),
                    "APPS": configs,
                },
            }
        return {}

    def get_provider_import_paths(self):
        return [self.get("module-path", self._module_path)]
