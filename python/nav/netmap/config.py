from nav.config import NavConfigParserDefaultSection


class NetmapConfig(NavConfigParserDefaultSection):
    """NetmapConfig"""

    DEFAULT_CONFIG_FILES = ('netmap.conf',)
    DEFAULT_CONFIG = """
[netmap]
API_DEBUG=False
"""


NETMAP_CONFIG = NetmapConfig("netmap")
