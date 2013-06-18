#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
# Copyright (C) 2006, 2007, 2009, 2011, 2013 UNINETT AS
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
"""This package encompasses modules with web functionality for NAV"""
import ConfigParser
import os.path
import cgi
import logging

import nav
import nav.path
from nav.models.profiles import Account


logger = logging.getLogger("nav.web")
webfrontConfig = ConfigParser.ConfigParser()
webfrontConfig.read(os.path.join(nav.path.sysconfdir, 'webfront',
                                 'webfront.conf'))


def should_show(url, user):
    """Verifies whether a hyperlink should be shown to a specific user.

    When a user doesn't have the proper permissions to visit a specific NAV
    URL, it doesn't always make sense to display a link to that URL in the
    interface. This function can be used to make a decision of whether to
    display such a link or not.

    Any url that starts with `http://` or `https://` is considered an
    external link and allowed. Relative URLs are checked against the user's
    privileges.

    :param url: An URL string to check for access
    :param user: A user dictionary from a web session
    :return: True if a hyperlink to `url` should be shown to `user`

    """
    starts_with_http = (url.lower().startswith('http://') or
                        url.lower().startswith('https://'))

    try:
        return (starts_with_http or
                Account.objects.get(id=user['id']).has_perm('web_access', url))
    except Account.DoesNotExist:
        return False


def escape(s):
    """Replace special characters '&', '<' and '>' by SGML entities.
    Wraps cgi.escape, but allows False values of s to be converted to
    empty strings."""
    if s:
        return cgi.escape(str(s))
    else:
        return ''
