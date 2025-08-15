#
# Copyright (C) 2006, 2007, 2009, 2011, 2013, 2018 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""This package encompasses modules with web functionality for NAV"""

import logging
import sys

import os.path

from django.http import HttpResponse

import nav.logs
from nav.config import NAVConfigParser


_logger = logging.getLogger(__name__)

# Set default config params and read rest from file


class WebfrontConfigParser(NAVConfigParser):
    DEFAULT_CONFIG_FILES = [os.path.join('webfront', 'webfront.conf')]
    DEFAULT_CONFIG = """
[qr_codes]
file_format = png
"""

    def __init__(self):
        super(WebfrontConfigParser, self).__init__()

        self.validate_qr_codes_config()

    def validate_qr_codes_config(self):
        allowed_file_formats = ["png", "svg"]

        file_format = self.get("qr_codes", "file_format")
        file_format = file_format.lower()

        if file_format not in allowed_file_formats:
            file_format = "png"
        self.set("qr_codes", "file_format", file_format)


webfrontConfig = WebfrontConfigParser()


def refresh_session(request):
    """Forces a refresh of the session by setting the modified flag"""
    request.session.modified = True
    _logger.debug('refresh_session: refreshed')
    return HttpResponse()


def loginit():
    """Initialize a logging setup for the NAV web interface.

    All logging is directed to stderr, which should end up in Apache's
    error log.

    """
    global _loginited
    try:
        # Make sure we don't initialize logging setup several times (in case
        # of module reloads and such)
        if _loginited:
            return
    except NameError:
        pass

    root = logging.getLogger('')

    # Attempt to mimic Apache's standard log time format
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [pid=%(process)d %(name)s] %(message)s",
        "%a %b %d %H:%M:%S %Y",
    )
    try:
        handler = logging.StreamHandler(sys.stderr)
    except IOError:
        # Something went terribly wrong. Maybe stderr is closed?
        # We silently ignore it and log nothing :-P
        pass
    else:
        handler.setFormatter(formatter)

        root.addHandler(handler)
        nav.logs.set_log_config()
        _loginited = True
