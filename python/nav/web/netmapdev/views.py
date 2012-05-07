#
# Copyright (C) 2007, 2010, 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Netmap mod_python handler"""

import nav.db
import psycopg2.extras

from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.http import Http404
from django.core.urlresolvers import reverse

from nav.django.shortcuts import render_to_response
from nav.django.utils import get_account

from nav.web.netmap.datacollector import getData

from nav.web.templates.GraphML import GraphML
from nav.web.templates.Netmapdev import Netmapdev


def index(request):
    """The main Netmap view, embedding the Java applet"""
    #page = Netmapdev()
    #page.sessionID = _get_session_cookie(req)
    #base_url = req.build_absolute_uri()
    #page.baseURL = base_url[:-1]
    #account = get_account(req)
    #if account.has_perm(None, None):
    #    page.is_admin = "True"
    #else:
    #    page.is_admin = "False"

    return render_to_response(Netmapdev,
                              'netmapdev/index.html',
                              { },
                              RequestContext(request),
                              path=[('Home', '/'),
                                    ('Netmapdev', None)])




class HttpResponseUnauthorized(HttpResponse):
    """A HttpResponse defaulting to a 401 UNAUTHORIZED status code"""
    def __init__(self):
        super(HttpResponseUnauthorized, self).__init__()
        self.status_code = 401
