# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""Django URL configuration"""

from django.conf.urls.defaults import patterns, url

def get_urlpatterns():
    """
    URL patterns for non-Django subsystems

    An alternative to nav.web.urlbuilder for linking from Django apps to
    non-Django parts of NAV in the normal Django way.

    """

    # Dummy view
    dummy = lambda *args, **kwargs: None

    urlpatterns = patterns('',
        # Subsystem: Device History
        url(r'^devicemanagement/$', dummy, name='devicemanagement'),
        url(r'^devicemanagement/\?view_netbox=(?P<netbox_id>\d+)$',
            dummy, name='devicemanagement-history-netbox'),

    )

    return urlpatterns
