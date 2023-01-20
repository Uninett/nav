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
                aud = self._validate_audience(get('aud'))
                key_type = self._validate_type(get('keytype'))
                if key_type == 'PEM':
                    key = self._read_file(key)
                claims_options = {
                    'aud': {'values': [aud], 'essential': True},
                }
                issuers_settings[section] = {
                    'key': key,
                    'type': key_type,
                    'claims_options': claims_options,
                }
            except (configparser.Error, ConfigurationError) as error:
                _logger.error('Error collecting stats for %s: %s', section, error)
        return issuers_settings

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

    def _validate_audience(self, audience):
        if not audience:
            raise ConfigurationError("Invalid 'aud': 'aud' must not be empty")
        return audience
