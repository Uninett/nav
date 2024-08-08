import logging
from os.path import join
from functools import partial
import configparser
from typing import Any
from datetime import timedelta

from nav.config import ConfigurationError, NAVConfigParser

_logger = logging.getLogger('nav.jwtconf')

ACCESS_TOKEN_EXPIRE_DELTA = timedelta(hours=1)
REFRESH_TOKEN_EXPIRE_DELTA = timedelta(days=1)


class JWTConf(NAVConfigParser):
    """webfront/jwt.conf config parser"""

    DEFAULT_CONFIG_FILES = [join('webfront', 'jwt.conf')]
    NAV_SECTION = "nav"

    def get_issuers_setting(self) -> dict[str, Any]:
        """Parses the webfront/jwt.conf config file and returns a dictionary that can
        be used as settings for the `drf-oidc-auth` django extension.
        If the parsing fails, an empty dict is returned.
        """
        try:
            external_settings = self._get_settings_for_external_tokens()
            local_settings = self._get_settings_for_nav_issued_tokens()
            external_settings.update(local_settings)
            return external_settings
        except ConfigurationError as error:
            _logger.error('Error reading jwtconfig: %s', error)
            return dict()

    def _get_settings_for_external_tokens(self):
        settings = dict()
        try:
            for section in self.sections():
                if section == self.NAV_SECTION:
                    continue
                get = partial(self.get, section)
                issuer = self._validate_issuer(section)
                key = self._validate_key(get('key'))
                aud = self._validate_audience(get('aud'))
                key_type = self._validate_type(get('keytype'))
                if key_type == 'PEM':
                    key = self._read_key_from_path(key)
                claims_options = {
                    'aud': {'values': [aud], 'essential': True},
                }
                settings[issuer] = {
                    'key': key,
                    'type': key_type,
                    'claims_options': claims_options,
                }
        except (
            configparser.NoSectionError,
            configparser.NoOptionError,
        ) as error:
            raise ConfigurationError(error)
        return settings

    def _read_key_from_path(self, path):
        try:
            with open(path, "r") as f:
                return f.read()
        except FileNotFoundError:
            raise ConfigurationError(
                "Could not find file %s to read PEM key from", path
            )
        except PermissionError:
            raise ConfigurationError(
                "Could not access file %s to read PEM key from", path
            )

    def _validate_key(self, key):
        if not key:
            raise ConfigurationError("Invalid 'key': 'key' must not be empty")
        return key

    def _validate_type(self, key_type):
        if key_type not in ['JWKS', 'PEM']:
            raise ConfigurationError(
                "Invalid 'keytype': 'keytype' must be either 'JWKS' or 'PEM'"
            )
        return key_type

    def _validate_issuer(self, section):
        if not section:
            raise ConfigurationError("Invalid 'issuer': 'issuer' must not be empty")
        try:
            nav_name = self.get_nav_name()
        except ConfigurationError:
            pass
        else:
            if section == nav_name:
                raise ConfigurationError(
                    "Invalid 'issuer': %s collides with internal issuer name %s",
                    section,
                )
        return section

    def _validate_audience(self, audience):
        if not audience:
            raise ConfigurationError("Invalid 'aud': 'aud' must not be empty")
        return audience

    def _get_nav_token_config_option(self, option):
        try:
            get = partial(self.get, self.NAV_SECTION)
            return get(option)
        except (
            configparser.NoSectionError,
            configparser.NoOptionError,
        ) as error:
            raise ConfigurationError(error)

    def get_nav_private_key(self):
        path = self._get_nav_token_config_option('private_key')
        return self._read_key_from_path(path)

    def get_nav_public_key(self):
        path = self._get_nav_token_config_option('public_key')
        return self._read_key_from_path(path)

    def get_nav_name(self):
        name = self._get_nav_token_config_option('name')
        if not name:
            raise ConfigurationError("Invalid 'name': 'name' must not be empty")
        return name

    def _get_settings_for_nav_issued_tokens(self):
        if not self.has_section(self.NAV_SECTION):
            return {}
        name = self.get_nav_name()
        claims_options = {
            'aud': {'values': [name], 'essential': True},
            'token_type': {'values': ['access_token'], 'essential': True},
        }
        settings = {
            name: {
                'type': "PEM",
                'key': self.get_nav_public_key(),
                'claims_options': claims_options,
            }
        }
        return settings
