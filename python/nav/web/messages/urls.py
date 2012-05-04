#
# Copyright (C) 2012 UNINETT AS
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

from django.conf.urls.defaults import url, patterns

from nav.web.messages.handler import rss, active, historic
from nav.web.messages.handler import new, edit, followup
from nav.web.messages.handler import planned, view, expire

urlpatterns = patterns('',

    #search
    url(r'^$', active,
        name='messages-active'),

    url(r'^active/$', active,
        name='messages-active'),

    url(r'^rss/$', rss,
        name='messages-rss'),

    url(r'^historic/$', historic,
        name='messages-historic'),

    url(r'^new/$', new,
        name='messages-new'),

    url(r'^edit/$', edit,
        name='messages-edit'),

    url(r'^followup/$', followup,
        name='messages-followup'),

    url(r'^planned/$', planned,
        name='messages-planned'),

    url(r'^view/$', view,
        name='messages-view'),

    url(r'^expire/$', expire,
        name='messages-expire'),
    )
