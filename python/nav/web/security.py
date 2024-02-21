from pathlib import Path

from nav.config import NAVConfigParser


class WebSecurityConfigParser(NAVConfigParser):
    DEFAULT_CONFIG_FILES = [str(Path('webfront') / 'webfront.conf')]
    DEFAULT_CONFIG = u"""
[security]
tls=off
"""
