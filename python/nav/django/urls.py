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

from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from nav.web.webfront.urls import urlpatterns

urlpatterns += patterns('',
    (r'^status/', include('nav.web.status.urls')),
    (r'^ajax/', include('nav.web.ajax.urls')),
    (r'^alertprofiles/', include('nav.web.alertprofiles.urls')),
    (r'^arnold/', include('nav.web.arnold.urls')),
    (r'^devicehistory/', include('nav.web.devicehistory.urls')),
    (r'^geomap/', include('nav.web.geomap.urls')),
    (r'^info/', include('nav.web.info.urls')),
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
    (r'^rrd/', include('nav.web.rrdviewer.urls')),
    (r'^seeddb/', include('nav.web.seeddb.urls')),
    (r'^stats/', include('nav.web.sortedstats.urls')),
    (r'^syslogger/', include('nav.web.syslogger.urls')),
    (r'^threshold/', include('nav.web.threshold.urls')),

    (r'^useradmin/', include('nav.web.useradmin.urls')),
    url(r'^userinfo/', 'nav.web.useradmin.views.userinfo', name='userinfo'),
)

if settings.DEBUG:
    from nav import buildconf
    from os.path import join

    # Serve static content via Django when debugging
    for media in ('style', 'js', 'images'):
        urlpatterns += patterns('',
            (r'^%s/(?P<path>.*)$' % media, 'django.views.static.serve',
             {'document_root': join(buildconf.webrootdir, media)}))
