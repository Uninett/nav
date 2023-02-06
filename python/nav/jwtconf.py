import logging
from functools import partial
import configparser

from nav.config import ConfigurationError, NAVConfigParser

_logger = logging.getLogger('nav.jwtconf')


class JWTConf(NAVConfigParser):
    """jwt.conf config parser"""

    DEFAULT_CONFIG_FILES = ('jwt.conf',)
    NAV_SECTION = "nav-config"
    DEFAULT_CONFIG = u"""
[nav-config]
private_key=
public_key=
name=
"""

    def get_issuers_setting(self):
        try:
            external_settings = self._get_settings_for_external_tokens()
            local_settings = self._get_settings_for_nav_issued_tokens()
            external_settings.update(local_settings)
            return external_settings
        except (
            FileNotFoundError,
            configparser.Error,
            configparser.NoSectionError,
            configparser.NoOptionError,
            ConfigurationError,
        ) as error:
            _logger.error('Error reading jwtconfig %s', error)
            return dict()

    def _get_settings_for_external_tokens(self):
        settings = dict()
        for section in self.sections():
            if section == self.NAV_SECTION:
                continue
            get = partial(self.get, section)
            issuer = self._validate_issuer(section)
            key = self._validate_key(get('key'))
            aud = self._validate_audience(get('aud'))
            key_type = self._validate_type(get('keytype'))
            if key_type == 'PEM':
                key = self._read_file(key)
            claims_options = {
                'aud': {'values': [aud], 'essential': True},
            }
            settings[issuer] = {
                'key': key,
                'type': key_type,
                'claims_options': claims_options,
            }
        return settings

    def _read_file(self, file):
        with open(file, "r") as f:
            return f.read()

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
        if section == self.get_nav_name():
            raise ConfigurationError(
                "Invalid 'issuer': {} collides with internal issuer name".format(
                    section
                )
            )
        return section

    def _validate_audience(self, audience):
        if not audience:
            raise ConfigurationError("Invalid 'aud': 'aud' must not be empty")
        return audience

    def _get_nav_token_config(self):
        return partial(self.get, self.NAV_SECTION)

    def get_nav_private_key(self):
        get = self._get_nav_token_config()
        path = get('private_key')
        return self._read_file(path)

    def get_nav_public_key(self):
        get = self._get_nav_token_config()
        path = get('public_key')
        return self._read_file(path)

    def get_nav_name(self):
        get = self._get_nav_token_config()
        name = get('name')
        if not name:
            raise ConfigurationError("Invalid 'name': 'name' must not be empty")
        return name

    def _get_settings_for_nav_issued_tokens(self):
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
