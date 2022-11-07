from os.path import isabs, join
from nav.config import NAVConfigParser, find_config_dir


class APIConfig(NAVConfigParser):
    DEFAULT_CONFIG_FILES = (join("api", "api.conf"),)
    DEFAULT_CONFIG = """
[keys]
public_key=jwtRS256.key.pub
"""

    def get_public_key(self):
        self.get_key('public_key')

    def get_key(self, key_name):
        path = self.get('keys', key_name)
        if not isabs(path):
            path = join(find_config_dir(), "api", path)
        with open(path) as f:
            return f.read()


API_CONF = APIConfig()
