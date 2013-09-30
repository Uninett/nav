#
# Copyright (C) 2013 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Impersonate Cricket with NAV's authentication and authorization in front.

Use as CGI front to Cricket's grapher.cgi.
"""
import warnings
warnings.simplefilter("ignore")

import os
import re
import logging
import StringIO

from nav.django.auth import AuthenticationMiddleware, AuthorizationMiddleware
import nav.logs
from nav.buildconf import CRICKETDIR
from nav.util import which

from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.sessions.middleware import SessionMiddleware
from django.conf import settings

CRICKET_GRAPHER = 'grapher.cgi'
SEARCH_PATH = [CRICKETDIR, '/usr/lib/cgi-bin/cricket', '/home/cricket']
INDEX_PATTERN = re.compile(r'/index.cgi$')
_logger = logging.getLogger(__name__)


def main():
    """Main CGI execution point"""
    logging.basicConfig()
    nav.logs.set_log_levels()

    if settings.DEBUG:
        import cgitb
        cgitb.enable()

    if cgi_verify_authorization():
        # Out with this shit, in with Cricket's grapher!
        search_path = SEARCH_PATH + os.environ.get('PATH', '').split(':')
        grapher = which(CRICKET_GRAPHER, search_path)
        if grapher:
            os.execvp(grapher, (grapher,))
        else:
            raise Exception("Unable to find an executable grapher.cgi "
                            "in any of %r" % search_path)


# pylint: disable=E1101
def cgi_verify_authorization():
    """
    Runs the appropriate Django/NAV middleware to authenticate and
    authorize the current CGI request. If any of the middleware wants to
    interfere with the request processing, the response is mirrored to the
    CGI client.

    """
    environ = dict(os.environ.items())
    environ['SCRIPT_NAME'] = INDEX_PATTERN.sub(
        '', environ.get('SCRIPT_NAME', ''))
    environ['wsgi.input'] = StringIO.StringIO()
    req = WSGIRequest(environ)

    for ware in (
        SessionMiddleware(),
        AuthenticationMiddleware(),
        AuthorizationMiddleware(),
    ):
        result = ware.process_request(req)
        _logger.debug("result of %r: %r", ware, result)
        if isinstance(result, HttpResponse):
            print "Status: %s" % result.status_code
            print str(result)
            return False

    return True


if __name__ == '__main__':
    main()
