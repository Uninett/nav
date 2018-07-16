#
# Copyright (C) 2006, 2007, 2009, 2011, 2013, 2018 Uninett AS
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
import configparser
import os.path

from django.http import HttpResponse

import nav.buildconf


webfrontConfig = configparser.ConfigParser()
webfrontConfig.read(os.path.join(nav.buildconf.sysconfdir, 'webfront',
                                 'webfront.conf'))


def refresh_session(request):
    """Forces a refresh of the session by setting the modified flag"""
    request.session.modified = True
    return HttpResponse()
