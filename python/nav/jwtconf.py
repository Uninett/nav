import logging
from functools import partial
import configparser

from nav.config import ConfigurationError, NAVConfigParser

_logger = logging.getLogger('nav.jwtconf')


class JWTConf(NAVConfigParser):
    """ipdevpoll config parser"""

    DEFAULT_CONFIG_FILES = ('jwt.conf',)

    def get_issuers_setting(self):
        issuers_settings = dict()
        for section in self.sections():
            try:
                get = partial(self.get, section)
                if get('type') not in ['JWKS', 'PEM']:
                    raise ConfigurationError(
                        "Invalid 'type' in section %s: 'type' must be either 'JWKS' or 'PEM'"
                        % section
                    )
                if not get('key'):
                    raise ConfigurationError(
                        "Invalid 'key' in section %s: 'key' must not be empty" % section
                    )
                if not get('audience'):
                    raise ConfigurationError(
                        "Invalid 'audience' in section %s: 'audience' must not be empty"
                        % section
                    )
                issuers_settings[section] = {
                    'type': get('type'),
                    'key': get('key'),
                    'aud': get('audience'),
                }
            except (configparser.Error) as error:
                _logger.error('Error collecting stats for %s: %s', section, error)
        return issuers_settings
