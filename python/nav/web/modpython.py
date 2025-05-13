#
# Copyright (C) 2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Functionality to enable any Apache-served resources to be protected by
NAV's authentication and authorization system, by the use of mod_python.

To protect a resource served by Apache using this module, add something like
the following to your Apache-config::

  <Location /protected-resource>
      PythonHeaderParserHandler nav.web.modpython
  </Location>


Known issues
------------

mod_python itself is no longer maintained, and therefore deprecated,
which is why the rest of NAV has completely moved to Django,
with a suggested WSGI-based configuration.

"""

import warnings
import logging
from http import cookies

from nav.bootstrap import bootstrap_django

from django.contrib.sessions.middleware import SessionMiddleware
from nav.web.auth.middleware import AuthenticationMiddleware, AuthorizationMiddleware
from nav.web import loginit
from django.db import connection


def headerparserhandler(req):
    """A mod_python headerparserhandler to authenticate and authorize a request
    using NAV.

    It uses NAV's Django authenticaton and authorization middlewares and
    translates between mod_python and Django requests/responses.

    """
    from mod_python import apache

    req.get_full_path = lambda: req.unparsed_uri
    is_ajax = req.headers_in.get('X-Requested-With', '') == 'XMLHttpRequest'
    req.is_ajax = lambda: is_ajax
    req.COOKIES = _get_cookie_dict(req)

    for mware in (SessionMiddleware, AuthenticationMiddleware, AuthorizationMiddleware):
        response = mware().process_request(req)

    try:
        if response:
            if 'Location' in response:
                req.headers_out['Location'] = response['Location']
            return response.status_code
        else:
            return apache.OK
    finally:
        # ensure we don't leak database connections. it's inefficient, yes, but
        # that's the price you pay for authorizing access to your other crap
        connection.close()


def _get_cookie_dict(req):
    if 'Cookie' in req.headers_in:
        cookie = cookies.SimpleCookie()
        cookie.load(str(req.headers_in['Cookie']))
        return dict((key, c.value) for key, c in cookie.items())
    else:
        return {}


#
# module initializations
#
# we try to filter out stupid warnings from third party libraries that end up
# in the apache logs. it won't help on first invocation though,
# since the errors are in mod_python itself, and mod_python is used to load
# this module.
#
warnings.filterwarnings("ignore", category=DeprecationWarning)
bootstrap_django()

loginit()
_logger = logging.getLogger(__name__)
