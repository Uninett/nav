#
# Copyright (C) 2007-2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
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
import logging
from django.conf.urls import include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from nav.config import find_config_dir
from nav.web import refresh_session
from nav.web.webfront.urls import urlpatterns
from nav.web.styleguide import styleguide_index
from nav.django.views import force_500

_logger = logging.getLogger(__name__)

urlpatterns += [
    url(r'^status/', include('nav.web.status2.urls')),
    url(r'^ajax/', include('nav.web.ajax.urls')),
    url(r'^business/', include('nav.web.business.urls')),
    url(r'^alertprofiles/', include('nav.web.alertprofiles.urls')),
    url(r'^api/', include('nav.web.api.urls', namespace='api')),
    url(r'^arnold/', include('nav.web.arnold.urls')),
    url(r'^devicehistory/', include('nav.web.devicehistory.urls')),
    url(r'^geomap/', include('nav.web.geomap.urls')),
    url(r'^search/', include('nav.web.info.urls')),
    url(r'^ipdevinfo/', include('nav.web.ipdevinfo.urls')),
    url(r'^l2trace/', include('nav.web.l2trace.urls')),
    url(r'^machinetracker/', include('nav.web.machinetracker.urls')),
    url(r'^macwatch/', include('nav.web.macwatch.urls')),
    url(r'^maintenance/', include('nav.web.maintenance.urls')),
    url(r'^messages/', include('nav.web.messages.urls')),
    url(r'^neighbors/', include('nav.web.neighbors.urls')),
    url(r'^netmap/', include('nav.web.netmap.urls')),
    url(r'^networkexplorer/', include('nav.web.networkexplorer.urls')),
    url(r'^portadmin/', include('nav.web.portadmin.urls')),
    url(r'^radius/', include('nav.web.radius.urls')),
    url(r'^report/', include('nav.web.report.urls')),
    url(r'^seeddb/', include('nav.web.seeddb.urls')),
    url(r'^stats/', include('nav.web.sortedstats.urls')),
    url(r'^syslogger/', include('nav.web.syslogger.urls')),
    url(r'^ipam/', include('nav.web.ipam.urls')),
    url(r'^threshold/', include('nav.web.threshold.urls')),
    url(r'^graphite/', include('nav.web.graphite.urls')),
    url(r'^navlets/', include('nav.web.navlets.urls')),
    url(r'^watchdog/', include('nav.web.watchdog.urls')),
    url(r'^useradmin/', include('nav.web.useradmin.urls')),
    url(r'^styleguide/', styleguide_index),
    url(r'^refresh_session/', refresh_session, name='refresh-session'),
    url(r'^auditlog/', include('nav.auditlog.urls')),
    url(r'^interfaces/', include('nav.web.interface_browser.urls')),
    url(r'^500/', force_500),
]

# Load local url-config
_local_python_dir = os.path.join(find_config_dir() or '.', 'python')
_local_url_filepath = os.path.join(_local_python_dir, 'local_urls.py')

if os.path.isfile(_local_url_filepath):
    if _local_python_dir not in sys.path:
        sys.path.append(_local_python_dir)
    try:
        import local_urls
        urlpatterns += local_urls.urlpatterns
    except (ImportError, TypeError):
        _logger.exception("failed to import urlpatterns from local_urls.py")
        pass

handler500 = 'nav.django.views.custom_500'

# Make django serve static files (a webserver like apache overrides this)
urlpatterns += staticfiles_urlpatterns()
