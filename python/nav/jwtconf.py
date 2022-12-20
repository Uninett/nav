import logging
from functools import partial
import configparser

from nav.config import ConfigurationError, NAVConfigParser

_logger = logging.getLogger('nav.jwtconf')


class JWTConf(NAVConfigParser):
    """jwt.conf config parser"""

    DEFAULT_CONFIG_FILES = ('jwt.conf',)

    def get_issuers_setting(self):
        issuers_settings = dict()
        for section in self.sections():
            try:
                get = partial(self.get, section)
                key = self._validate_key(get('key'))
                aud = self._validate_key(get('audience'))
                key_type = self._validate_key(get('keytype'))
                if key == 'PEM':
                    with open("demofile.txt", "r") as f:
                        key = f.read()
                issuers_settings[section] = {
                    'key': key,
                    'type': key_type,
                    'aud': aud,
                }
            except (configparser.Error, ConfigurationError) as error:
                _logger.error('Error collecting stats for %s: %s', section, error)
        return issuers_settings

    def _validate_key(self, key):
        if not key:
            raise ConfigurationError("Invalid 'key': 'key' must not be empty")
        return key

    def _validate_type(self, key_type):
        if key_type not in ['JWKS', 'PEM']:
            raise ConfigurationError(
                "Invalid 'type': 'type' must be either 'JWKS' or 'PEM'"
            )
        return key_type

    def _validate_audience(self, audience):
        if not audience:
            raise ConfigurationError("Invalid 'audience': 'audience' must not be empty")
        return audience
