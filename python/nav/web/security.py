from pathlib import Path

from nav.config import NavConfigParserDefaultSection


class WebSecurityConfigParser(NavConfigParserDefaultSection):
    SECTION = "security"
    DEFAULT_CONFIG_FILES = [str(Path('webfront') / 'webfront.conf')]
    DEFAULT_CONFIG = """
[security]
needs_tls=no
allow_frames=self
"""
    FRAMES_OPTION = 'allow_frames'
    FRAMES_DEFAULT = 'self'

    def __init__(self):
        super().__init__(self.SECTION)

    # clickjacking-settings

    def get_x_frame_options(self):
        "Translate CSP frame ancestors to the old X-Frame-Options header"
        frames_flag = self.get(self.FRAMES_OPTION) or self.FRAMES_DEFAULT
        if frames_flag == 'none':
            return 'DENY'
        return 'SAMEORIGIN'
