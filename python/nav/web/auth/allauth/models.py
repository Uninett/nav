#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Pydantic models for authentication configuration.

Replaces the TOMLConfigParser-based parsers for reading
``webfront/authentication.toml``.
"""

import logging
import tomllib
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from nav.config import find_config_file

_logger = logging.getLogger(__name__)


# --- Shared alias helpers ---------------------------------------------------


def _to_hyphen(name: str) -> str:
    """Convert underscored Python names to hyphenated TOML keys."""
    return name.replace("_", "-")


HYPHENATED = ConfigDict(
    extra="forbid",
    alias_generator=_to_hyphen,
    populate_by_name=True,
)


# --- MFA -------------------------------------------------------------------


class MFAConfig(BaseModel):
    """Multi-factor authentication settings from ``[multi-factor-authentication]``."""

    model_config = HYPHENATED

    enabled: bool = False
    support_recovery_codes: bool = True
    support_passkeys: bool = False
    support_passkey_signups: bool = False
    allow_insecure_origin: bool = False

    def get_MFA_SUPPORTED_TYPES_setting(self) -> list[str]:
        """Return the value for Django's ``MFA_SUPPORTED_TYPES`` setting."""
        methods = []
        if self.enabled:
            methods.append("totp")
            if self.support_recovery_codes:
                methods.append("recovery_codes")
            if self.support_passkeys:
                methods.append("passkeys")
        return methods

    def get_MFA_PASSKEY_LOGIN_ENABLED_setting(self) -> bool:
        """Return the value for Django's ``MFA_PASSKEY_LOGIN_ENABLED`` setting."""
        return self.enabled and self.support_passkeys

    def get_MFA_PASSKEY_SIGNUP_ENABLED_setting(self) -> bool:
        """Return the value for Django's ``MFA_PASSKEY_SIGNUP_ENABLED`` setting."""
        return (
            self.get_MFA_PASSKEY_LOGIN_ENABLED_setting()
            and self.support_passkey_signups
        )

    def get_MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN_setting(self) -> bool:
        """Return the value for the ``MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN`` setting."""
        return (
            self.get_MFA_PASSKEY_LOGIN_ENABLED_setting() and self.allow_insecure_origin
        )


# --- Social providers -------------------------------------------------------


class SocialProviderEntry(BaseModel):
    """A single social-login provider entry from ``[social.providers.<id>]``.

    Example:

    [social.providers.dataporten]
    client-id = "for this specific provider, this is a uuid"
    secret = "for this specific provider, this is a uuid"
    scope = ["userid-feide"]  # to get the Feide id
    module-path = "allauth.socialaccount.providers.dataporten"
    """

    model_config = HYPHENATED

    client_id: str
    secret: str
    scope: list[str] = []
    module_path: str
    settings: dict[str, Any] = {}


class SocialConfig(BaseModel):
    """Social-login provider settings from ``[social]``."""

    model_config = ConfigDict(extra="forbid")

    providers: dict[str, SocialProviderEntry] = {}

    def generate_SOCIALACCOUNT_PROVIDERS(self) -> dict:
        """Translate configured providers into a ``SOCIALACCOUNT_PROVIDERS`` dict."""
        configs: dict[str, Any] = {}
        for provider_id, entry in self.providers.items():
            config: dict[str, Any] = {}
            if entry.scope:
                config["SCOPE"] = entry.scope

            app: dict[str, Any] = {
                "client_id": entry.client_id,
                "secret": entry.secret,
            }
            if entry.settings:
                app["settings"] = entry.settings
            config["APP"] = app
            configs[provider_id] = config
        return configs

    def get_provider_import_paths(self) -> list[str]:
        """Return dotted import paths for each configured provider."""
        return [entry.module_path for entry in self.providers.values()]


# --- OIDC providers ---------------------------------------------------------


class OIDCProviderSettings(BaseModel):
    """Provider-specific OIDC settings from ``[oidc.idps.<id>.settings]``.

    Uses ``extra="allow"`` because OIDC settings carry arbitrary
    provider-specific keys through to allauth.
    """

    model_config = ConfigDict(extra="allow")

    uid_field: str = "sub"


class OIDCProviderEntry(BaseModel):
    """A single OIDC identity provider entry from ``[oidc.idps.<id>]``."""

    model_config = ConfigDict(extra="forbid")

    name: str
    client_id: str
    secret: str
    server_url: str
    settings: OIDCProviderSettings = OIDCProviderSettings()


class OIDCConfig(BaseModel):
    """OpenID Connect provider settings from ``[oidc]``."""

    model_config = HYPHENATED

    module_path: str = "allauth.socialaccount.providers.openid_connect"
    oauth_pkce_enabled: bool = False
    idps: dict[str, OIDCProviderEntry] = {}

    def generate_SOCIALACCOUNT_PROVIDERS(self) -> dict:
        """Translate configured IDPs into a ``SOCIALACCOUNT_PROVIDERS`` dict."""
        apps = []
        for provider_id, entry in self.idps.items():
            settings: dict[str, Any] = {
                "server_url": entry.server_url,
                "uid_field": entry.settings.uid_field,
            }
            # Pass through any extra provider-specific settings
            settings.update(entry.settings.model_extra)

            app: dict[str, Any] = {
                "provider_id": provider_id,
                "name": entry.name,
                "client_id": entry.client_id,
                "secret": entry.secret,
                "settings": settings,
            }
            apps.append(app)

        if apps:
            return {
                "openid_connect": {
                    "OAUTH_PKCE_ENABLED": self.oauth_pkce_enabled,
                    "APPS": apps,
                },
            }
        return {}

    def get_provider_import_paths(self) -> list[str]:
        """Return the OIDC provider module path, or empty if no IDPs configured."""
        if self.idps:
            return [self.module_path]
        return []


# --- Root model + file reader -----------------------------------------------


class AuthenticationConfig(BaseModel):
    """Root model for ``webfront/authentication.toml``."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    mfa: MFAConfig = Field(
        default_factory=MFAConfig, alias="multi-factor-authentication"
    )
    social: SocialConfig = Field(default_factory=SocialConfig)
    oidc: OIDCConfig = Field(default_factory=OIDCConfig)


def read_authentication_config(
    config_file: str = "webfront/authentication.toml",
) -> AuthenticationConfig:
    """Read and validate the authentication TOML config file.

    :param config_file: Path relative to the NAV config directory.
    :returns: Parsed configuration, or all defaults if the file is not found.
    :raises pydantic.ValidationError: If the file contains invalid keys or
        values (a friendly message is logged before re-raising).
    """
    path = find_config_file(config_file)
    if not path:
        _logger.info(
            "Authentication config file %s not found, using defaults",
            config_file,
        )
        return AuthenticationConfig()

    with open(path, "rb") as fh:
        raw = tomllib.load(fh)

    try:
        return AuthenticationConfig.model_validate(raw)
    except ValidationError as exc:
        _logger.error(
            "Validation errors in %s:\n%s",
            path,
            format_validation_error(exc),
        )
        raise


def format_validation_error(exc: ValidationError) -> str:
    """Return operator-friendly error lines from a ``ValidationError``.

    Each Pydantic error is rendered as ``section.key: message``.

    :param exc: The caught validation error.
    :returns: A newline-separated string of error descriptions.
    """
    lines = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"])
        lines.append(f"  {location}: {error['msg']}")
    return "\n".join(lines)
