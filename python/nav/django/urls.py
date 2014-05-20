#
# Copyright (C) 2007-2013 UNINETT AS
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
"""Main Django URL configuration"""

import sys
import os
import nav
from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from nav.web.webfront.urls import urlpatterns
from nav.web.styleguide import styleguide_index

urlpatterns += patterns('',
    (r'^status/', include('nav.web.status.urls')),
    (r'^ajax/', include('nav.web.ajax.urls')),
    (r'^alertprofiles/', include('nav.web.alertprofiles.urls')),
    (r'^api/', include('nav.web.api.urls', namespace='api')),
    (r'^arnold/', include('nav.web.arnold.urls')),
    (r'^devicehistory/', include('nav.web.devicehistory.urls')),
    (r'^geomap/', include('nav.web.geomap.urls')),
    (r'^search/', include('nav.web.info.urls')),
    (r'^ipdevinfo/', include('nav.web.ipdevinfo.urls')),
    (r'^l2trace/', include('nav.web.l2trace.urls')),
    (r'^machinetracker/', include('nav.web.machinetracker.urls')),
    (r'^macwatch/', include('nav.web.macwatch.urls')),
    (r'^maintenance/', include('nav.web.maintenance.urls')),
    (r'^messages/', include('nav.web.messages.urls')),
    (r'^netmap/', include('nav.web.netmap.urls')),
    (r'^networkexplorer/', include('nav.web.networkexplorer.urls')),
    (r'^portadmin/', include('nav.web.portadmin.urls')),
    (r'^powersupplies/', include('nav.web.powersupplies.urls')),
    (r'^radius/', include('nav.web.radius.urls')),
    (r'^report/', include('nav.web.report.urls')),
    (r'^seeddb/', include('nav.web.seeddb.urls')),
    (r'^stats/', include('nav.web.sortedstats.urls')),
    (r'^syslogger/', include('nav.web.syslogger.urls')),
    (r'^threshold/', include('nav.web.threshold.urls')),
    (r'^graphite/', include('nav.web.graphite.urls')),
    (r'^navlets/', include('nav.web.navlets.urls')),
    (r'^watchdog/', include('nav.web.watchdog.urls')),

    (r'^useradmin/', include('nav.web.useradmin.urls')),
    (r'^styleguide/', styleguide_index),
)

# Load local url-config
_local_url_filepath = os.path.join(nav.buildconf.sysconfdir, 'python',
                                   'local_urls.py')
if os.path.isfile(_local_url_filepath):
    sys.path.append(_local_url_filepath)
    try:
        import local_urls
        urlpatterns += local_urls.urlpatterns
    except (ImportError, TypeError):
        pass

handler500 = 'nav.django.views.custom_500'

# Make django serve static files (a webserver like apache overrides this)
urlpatterns += staticfiles_urlpatterns()
