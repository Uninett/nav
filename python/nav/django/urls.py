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
from django.urls import re_path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from nav.config import find_config_dir
from nav.web import refresh_session
from nav.web.webfront.urls import urlpatterns
from nav.web.styleguide import styleguide_index
from nav.django.views import force_500

_logger = logging.getLogger(__name__)

urlpatterns += [
    re_path(r'^status/', include('nav.web.status2.urls')),
    re_path(r'^ajax/', include('nav.web.ajax.urls')),
    re_path(r'^business/', include('nav.web.business.urls')),
    re_path(r'^alertprofiles/', include('nav.web.alertprofiles.urls')),
    re_path(r'^api/', include(('nav.web.api.urls', 'api'))),
    # re_path(r'^api/', include(('nav.web.api.urls', 'api'), namespace='api')),
    re_path(r'^arnold/', include('nav.web.arnold.urls')),
    re_path(r'^devicehistory/', include('nav.web.devicehistory.urls')),
    re_path(r'^geomap/', include('nav.web.geomap.urls')),
    re_path(r'^search/', include('nav.web.info.urls')),
    re_path(r'^ipdevinfo/', include('nav.web.ipdevinfo.urls')),
    re_path(r'^l2trace/', include('nav.web.l2trace.urls')),
    re_path(r'^machinetracker/', include('nav.web.machinetracker.urls')),
    re_path(r'^macwatch/', include('nav.web.macwatch.urls')),
    re_path(r'^maintenance/', include('nav.web.maintenance.urls')),
    re_path(r'^messages/', include('nav.web.messages.urls')),
    re_path(r'^neighbors/', include('nav.web.neighbors.urls')),
    re_path(r'^netmap/', include('nav.web.netmap.urls')),
    re_path(r'^networkexplorer/', include('nav.web.networkexplorer.urls')),
    re_path(r'^portadmin/', include('nav.web.portadmin.urls')),
    re_path(r'^radius/', include('nav.web.radius.urls')),
    re_path(r'^report/', include('nav.web.report.urls')),
    re_path(r'^seeddb/', include('nav.web.seeddb.urls')),
    re_path(r'^stats/', include('nav.web.sortedstats.urls')),
    re_path(r'^syslogger/', include('nav.web.syslogger.urls')),
    re_path(r'^ipam/', include('nav.web.ipam.urls')),
    re_path(r'^threshold/', include('nav.web.threshold.urls')),
    re_path(r'^graphite/', include('nav.web.graphite.urls')),
    re_path(r'^navlets/', include('nav.web.navlets.urls')),
    re_path(r'^watchdog/', include('nav.web.watchdog.urls')),
    re_path(r'^useradmin/', include('nav.web.useradmin.urls')),
    re_path(r'^styleguide/', styleguide_index),
    re_path(r'^refresh_session/', refresh_session, name='refresh-session'),
    re_path(r'^auditlog/', include('nav.auditlog.urls')),
    re_path(r'^interfaces/', include('nav.web.interface_browser.urls')),
    re_path(r'^500/', force_500),
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
