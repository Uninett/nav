from pathlib import Path

from nav.config import NavConfigParserDefaultSection


class WebSecurityConfigParser(NavConfigParserDefaultSection):
    SECTION = "security"
    DEFAULT_CONFIG_FILES = [str(Path('webfront') / 'webfront.conf')]
    DEFAULT_CONFIG = u"""
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

    def get_frame_ancestors(self):
        """Return a list of sources

        A single 'none' or a string of one or more of self, source-scheme and
        host-scheme are valid. There is currently no validator for host-scheme,
        so source-scheme and host-scheme are both outputted as-is.

        To be set in django settings and used by the django-csp middleware.
        """
        default = "'self'"
        frames_flag = self.get(self.FRAMES_OPTION) or self.FRAMES_DEFAULT
        pieces = frames_flag.split()
        valid_pieces = []
        for piece in pieces:
            if piece == 'none':
                valid_pieces.append("'none'")
                break
            if piece == 'self':
                valid_pieces.append(default)
            else:
                valid_pieces.append(piece)
        return valid_pieces or [default]
