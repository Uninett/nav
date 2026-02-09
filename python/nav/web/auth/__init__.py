# Copyright (C) 2010, 2011, 2013, 2019 Uninett AS
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
"""
Contains web authentication and login functionality for NAV.
"""

import logging
from urllib import parse

from django.http import HttpRequest

from nav.django.defaults import LOGIN_URL
from nav.web.auth import remote_user

_logger = logging.getLogger(__name__)


# This may seem like redundant information, but it seems django's reverse
# will hang under some usages of these middleware classes - so until we figure
# out what's going on, we'll hardcode this here.
# LOGIN_URL = '/accounts/login/'
# The local logout url, redirects to '/' after logout
# If the entire site is protected via remote_user, this link must be outside
# that protection!
LOGOUT_URL = '/index/logout/'


def get_login_url(request: HttpRequest, path=None) -> str:
    """Calculate which login_url to use"""
    if path is None:
        path = parse.quote(request.get_full_path())
    if path == "/":
        default_new_url = LOGIN_URL
    else:
        default_new_url = '{0}?origin={1}&noaccess'.format(LOGIN_URL, path)
    remote_loginurl = remote_user.CONFIG.get_loginurl(request)
    return remote_loginurl if remote_loginurl else default_new_url


def get_post_logout_redirect_url(request: HttpRequest) -> str:
    default = "/"
    redirect_url = remote_user.CONFIG.get_post_logout_redirect_url(request)
    return redirect_url if redirect_url else default


def get_logout_url(request: HttpRequest) -> str:
    """Calculate which logout_url to use"""
    remote_logouturl = remote_user.CONFIG.get_logouturl(request)
    if remote_logouturl and remote_logouturl.endswith('='):
        remote_logouturl += request.build_absolute_uri(LOGOUT_URL)
    return remote_logouturl if remote_logouturl else LOGOUT_URL
