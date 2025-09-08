#
# Copyright (C) 2007-2013 Uninett AS
# Copyright (C) 2022 Sikt
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
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from nav.config import find_config_dir
from nav.web import refresh_session
from nav.web.webfront.urls import urlpatterns
from nav.web.styleguide import styleguide_index
from nav.django.views import force_500

_logger = logging.getLogger(__name__)

urlpatterns += [
    path('status/', include('nav.web.status2.urls')),
    path('ajax/', include('nav.web.ajax.urls')),
    path('business/', include('nav.web.business.urls')),
    path('alertprofiles/', include('nav.web.alertprofiles.urls')),
    path('api/', include(('nav.web.api.urls', 'api'))),
    # path('api/', include(('nav.web.api.urls', 'api'), namespace='api')),
    path('arnold/', include('nav.web.arnold.urls')),
    path('devicehistory/', include('nav.web.devicehistory.urls')),
    path('geomap/', include('nav.web.geomap.urls')),
    path('search/', include('nav.web.info.urls')),
    path('ipdevinfo/', include('nav.web.ipdevinfo.urls')),
    path('l2trace/', include('nav.web.l2trace.urls')),
    path('machinetracker/', include('nav.web.machinetracker.urls')),
    path('macwatch/', include('nav.web.macwatch.urls')),
    path('maintenance/', include('nav.web.maintenance.urls')),
    path('messages/', include('nav.web.messages.urls')),
    path('neighbors/', include('nav.web.neighbors.urls')),
    path('netmap/', include('nav.web.netmap.urls')),
    path('networkexplorer/', include('nav.web.networkexplorer.urls')),
    path('portadmin/', include('nav.web.portadmin.urls')),
    path('radius/', include('nav.web.radius.urls')),
    path('report/', include('nav.web.report.urls')),
    path('seeddb/', include('nav.web.seeddb.urls')),
    path('stats/', include('nav.web.sortedstats.urls')),
    path('syslogger/', include('nav.web.syslogger.urls')),
    path('ipam/', include('nav.web.ipam.urls')),
    path('threshold/', include('nav.web.threshold.urls')),
    path('graphite/', include('nav.web.graphite.urls')),
    path('navlets/', include('nav.web.navlets.urls')),
    path('watchdog/', include('nav.web.watchdog.urls')),
    path('useradmin/', include('nav.web.useradmin.urls')),
    path('styleguide/', styleguide_index),
    path('refresh_session/', refresh_session, name='refresh-session'),
    path('auditlog/', include('nav.auditlog.urls')),
    path('interfaces/', include('nav.web.interface_browser.urls')),
    path('500/', force_500),
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
