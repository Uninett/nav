from os.path import isabs, join, dirname
from nav.config import ConfigurationError, NAVConfigParser, find_config_file


class APIConfig(NAVConfigParser):
    DEFAULT_CONFIG_FILES = (join("api", "api.conf"),)
    DEFAULT_CONFIG = u"""
[keys]
public_key=/etc/nav/api/jwtRS256.key.pub
"""

    def get_public_key(self):
        self.get_key('public_key')

    def get_key(self, key_name):
        path = self.get('keys', key_name)
        if not path:
            raise ConfigurationError(f"{key_name} is not configured")
        if not isabs(path):
            config_file = find_config_file(self.DEFAULT_CONFIG_FILES[0])
            if not config_file:
                raise FileNotFoundError(
                    f"Could not find {self.DEFAULT_CONFIG_FILES[0]}"
                )
            path = join(dirname(config_file), path)
        with open(path) as f:
            return f.read()


API_CONF = APIConfig()
