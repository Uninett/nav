"""Tests for Pydantic-based authentication config models."""

import tomllib
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from nav.web.auth.allauth.models import (
    AuthenticationConfig,
    MFAConfig,
    OIDCConfig,
    OIDCProviderEntry,
    OIDCProviderSettings,
    SocialConfig,
    SocialProviderEntry,
    format_validation_error,
    read_authentication_config,
)


class TestMFAConfig:
    def test_when_defaults_then_all_flags_should_match_expected(self):
        mfa = MFAConfig()
        assert mfa.enabled is False
        assert mfa.support_recovery_codes is True
        assert mfa.support_passkeys is False
        assert mfa.support_passkey_signups is False
        assert mfa.allow_insecure_origin is False

    def test_when_disabled_then_supported_types_should_be_empty(self):
        mfa = MFAConfig()
        assert mfa.get_MFA_SUPPORTED_TYPES_setting() == []

    def test_when_enabled_then_supported_types_should_include_totp_and_recovery(self):
        mfa = MFAConfig(enabled=True)
        assert mfa.get_MFA_SUPPORTED_TYPES_setting() == ["totp", "recovery_codes"]

    def test_when_enabled_with_passkeys_then_supported_types_should_include_passkeys(  # noqa: E501
        self,
    ):
        mfa = MFAConfig(enabled=True, support_passkeys=True)
        assert mfa.get_MFA_SUPPORTED_TYPES_setting() == [
            "totp",
            "recovery_codes",
            "passkeys",
        ]

    def test_when_enabled_without_recovery_codes_then_supported_types_should_exclude_them(  # noqa: E501
        self,
    ):
        mfa = MFAConfig(enabled=True, support_recovery_codes=False)
        assert mfa.get_MFA_SUPPORTED_TYPES_setting() == ["totp"]

    def test_when_disabled_then_passkey_login_should_be_false(self):
        mfa = MFAConfig(support_passkeys=True)
        assert mfa.get_MFA_PASSKEY_LOGIN_ENABLED_setting() is False

    def test_when_enabled_with_passkeys_then_passkey_login_should_be_true(self):
        mfa = MFAConfig(enabled=True, support_passkeys=True)
        assert mfa.get_MFA_PASSKEY_LOGIN_ENABLED_setting() is True

    def test_when_passkey_login_disabled_then_passkey_signup_should_be_false(self):
        mfa = MFAConfig(support_passkey_signups=True)
        assert mfa.get_MFA_PASSKEY_SIGNUP_ENABLED_setting() is False

    def test_when_passkey_login_enabled_then_passkey_signup_should_follow_flag(self):
        mfa = MFAConfig(
            enabled=True, support_passkeys=True, support_passkey_signups=True
        )
        assert mfa.get_MFA_PASSKEY_SIGNUP_ENABLED_setting() is True

    def test_when_passkey_login_disabled_then_insecure_origin_should_be_false(self):
        mfa = MFAConfig(allow_insecure_origin=True)
        assert mfa.get_MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN_setting() is False

    def test_when_passkey_login_enabled_then_insecure_origin_should_follow_flag(self):
        mfa = MFAConfig(enabled=True, support_passkeys=True, allow_insecure_origin=True)
        assert mfa.get_MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN_setting() is True

    def test_when_hyphenated_keys_then_it_should_parse_correctly(self):
        mfa = MFAConfig.model_validate(
            {
                "enabled": True,
                "support-passkeys": True,
                "support-recovery-codes": False,
            }
        )
        assert mfa.enabled is True
        assert mfa.support_passkeys is True
        assert mfa.support_recovery_codes is False


class TestSocialConfig:
    def test_when_empty_then_generate_should_return_empty_dict(self):
        sc = SocialConfig()
        assert sc.generate_SOCIALACCOUNT_PROVIDERS() == {}

    def test_when_providers_configured_then_generate_should_return_translated_config(
        self,
    ):
        config_string = """
[providers.testprovider1]
client_id = "not.optional"
secret = "not.optional"
scope = ["email"]
module-path = "allauth.socialaccount.providers.test1"

[providers.testprovider2]
client_id = "not.optional2"
secret = "not.optional2"
module-path = "allauth.socialaccount.providers.test2"

[providers.testprovider2.settings]
foo = 1
"""
        raw = tomllib.loads(config_string)
        sc = SocialConfig.model_validate(raw)
        expected = {
            "testprovider1": {
                "APP": {
                    "client_id": "not.optional",
                    "secret": "not.optional",
                },
                "SCOPE": ["email"],
            },
            "testprovider2": {
                "APP": {
                    "client_id": "not.optional2",
                    "secret": "not.optional2",
                    "settings": {
                        "foo": 1,
                    },
                },
            },
        }
        assert sc.generate_SOCIALACCOUNT_PROVIDERS() == expected

    def test_when_module_path_present_then_import_paths_should_include_it(self):
        sc = SocialConfig(
            providers={
                "github": SocialProviderEntry(
                    client_id="id",
                    secret="sec",
                    module_path="allauth.socialaccount.providers.github",
                ),
            }
        )
        assert sc.get_provider_import_paths() == [
            "allauth.socialaccount.providers.github"
        ]

    def test_when_module_path_missing_then_it_should_raise_validation_error(self):
        with pytest.raises(ValidationError):
            SocialProviderEntry(client_id="id", secret="sec")


class TestOIDCConfig:
    def test_when_empty_then_generate_should_return_empty_dict(self):
        oc = OIDCConfig()
        assert oc.generate_SOCIALACCOUNT_PROVIDERS() == {}

    def test_when_idps_configured_then_generate_should_return_translated_config(self):
        config_string = """
[idps.testprovider1]
name = "Provider 1"
client_id = "not.optional"
secret = "not.optional"
server_url = "https://server1.example.com"

[idps.testprovider1.settings]
foo = 1
"""
        raw = tomllib.loads(config_string)
        oc = OIDCConfig.model_validate(raw)
        expected = {
            "openid_connect": {
                "OAUTH_PKCE_ENABLED": False,
                "APPS": [
                    {
                        "provider_id": "testprovider1",
                        "name": "Provider 1",
                        "client_id": "not.optional",
                        "secret": "not.optional",
                        "settings": {
                            "server_url": "https://server1.example.com",
                            "uid_field": "sub",
                            "foo": 1,
                        },
                    },
                ],
            },
        }
        assert oc.generate_SOCIALACCOUNT_PROVIDERS() == expected

    def test_when_no_uid_field_set_then_it_should_fall_back_to_sub(self):
        oc = OIDCConfig(
            idps={
                "testprovider1": OIDCProviderEntry(
                    name="Provider 1",
                    client_id="not.optional",
                    secret="not.optional",
                    server_url="https://server1.example.com",
                ),
            }
        )
        result = oc.generate_SOCIALACCOUNT_PROVIDERS()
        settings = result["openid_connect"]["APPS"][0]["settings"]
        assert settings["uid_field"] == "sub"

    def test_when_pkce_enabled_then_generate_should_reflect_it(self):
        oc = OIDCConfig(
            oauth_pkce_enabled=True,
            idps={
                "test": OIDCProviderEntry(
                    name="Test",
                    client_id="id",
                    secret="sec",
                    server_url="https://example.com",
                ),
            },
        )
        result = oc.generate_SOCIALACCOUNT_PROVIDERS()
        assert result["openid_connect"]["OAUTH_PKCE_ENABLED"] is True

    def test_when_no_idps_then_import_paths_should_return_empty_list(self):
        oc = OIDCConfig()
        assert oc.get_provider_import_paths() == []

    def test_when_idps_present_then_import_paths_should_return_default_module(self):
        oc = OIDCConfig(
            idps={
                "test": OIDCProviderEntry(
                    name="Test",
                    client_id="id",
                    secret="sec",
                    server_url="https://example.com",
                ),
            }
        )
        assert oc.get_provider_import_paths() == [
            "allauth.socialaccount.providers.openid_connect"
        ]

    def test_when_custom_module_with_idps_then_import_paths_should_return_it(self):
        oc = OIDCConfig(
            module_path="custom.module",
            idps={
                "test": OIDCProviderEntry(
                    name="Test",
                    client_id="id",
                    secret="sec",
                    server_url="https://example.com",
                ),
            },
        )
        assert oc.get_provider_import_paths() == ["custom.module"]

    def test_when_scope_in_settings_then_generate_should_pass_it_through(self):
        oc = OIDCConfig(
            idps={
                "test": OIDCProviderEntry(
                    name="Test",
                    client_id="id",
                    secret="sec",
                    server_url="https://example.com",
                    settings=OIDCProviderSettings(scope=["openid", "email"]),
                ),
            },
        )
        result = oc.generate_SOCIALACCOUNT_PROVIDERS()
        settings = result["openid_connect"]["APPS"][0]["settings"]
        assert settings["scope"] == ["openid", "email"]


class TestAuthenticationConfig:
    def test_when_defaults_then_all_sections_should_have_defaults(self):
        config = AuthenticationConfig()
        assert config.mfa.enabled is False
        assert config.social.providers == {}
        assert config.oidc.idps == {}

    def test_when_extra_key_then_it_should_raise_validation_error(self):
        with pytest.raises(ValidationError):
            AuthenticationConfig.model_validate({"unknown_section": {}})

    def test_when_hyphenated_mfa_alias_then_it_should_parse_correctly(self):
        raw = {
            "multi-factor-authentication": {
                "enabled": True,
                "support-passkeys": True,
            }
        }
        config = AuthenticationConfig.model_validate(raw)
        assert config.mfa.enabled is True
        assert config.mfa.support_passkeys is True


class TestFormatValidationError:
    def test_when_validation_error_then_it_should_include_location_and_message(self):
        raw = {"multi-factor-authentication": {"bogus": True}}
        try:
            AuthenticationConfig.model_validate(raw)
        except ValidationError as exc:
            result = format_validation_error(exc)
        assert "multi-factor-authentication.bogus" in result
        assert "Extra inputs are not permitted" in result


class TestReadAuthenticationConfig:
    def test_when_file_not_found_then_it_should_return_defaults(self):
        with patch("nav.web.auth.allauth.models.find_config_file", return_value=None):
            config = read_authentication_config()
        assert config.mfa.enabled is False
        assert config.social.providers == {}
        assert config.oidc.idps == {}

    def test_when_valid_file_then_it_should_parse_correctly(self, tmp_path):
        toml_content = b"""
[multi-factor-authentication]
enabled = true
"""
        config_file = tmp_path / "authentication.toml"
        config_file.write_bytes(toml_content)

        with patch(
            "nav.web.auth.allauth.models.find_config_file",
            return_value=str(config_file),
        ):
            config = read_authentication_config()
        assert config.mfa.enabled is True

    def test_when_invalid_keys_then_it_should_raise_validation_error(self, tmp_path):
        toml_content = b"""
[multi-factor-authentication]
bogus-key = true
"""
        config_file = tmp_path / "authentication.toml"
        config_file.write_bytes(toml_content)

        with patch(
            "nav.web.auth.allauth.models.find_config_file",
            return_value=str(config_file),
        ):
            with pytest.raises(ValidationError):
                read_authentication_config()
