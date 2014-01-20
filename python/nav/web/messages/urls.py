#
# Copyright (C) 2013 UNINETT AS
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

from nav.web.messages.views import active, historic, planned
from nav.web.messages.views import save, followup, redirect_to_active
from nav.web.messages.views import view, expire
from nav.web.messages.feeds import ActiveMessagesFeed

urlpatterns = patterns('',

    url(r'^$', redirect_to_active),

    url(r'^active/$', active,
        name='messages-home'),

    url(r'^create/$', save,
        name='messages-create'),

    url(r'^edit/(?P<message_id>\d+)$', save,
        name='messages-edit'),

    url(r'^active/$', active,
        name='messages-active'),

    url(r'^scheduled/$', planned,
        name='messages-planned'),

    url(r'^archive/$', historic,
        name='messages-historic'),

    url(r'^view/(?P<message_id>\d+)$', view,
        name='messages-view'),

    url(r'^expire/(?P<message_id>\d+)$', expire,
        name='messages-expire'),

    url(r'^followup/(?P<message_id>\d+)$', followup,
        name='messages-followup'),

    url(r'^rss/$', ActiveMessagesFeed(),
        name='messages-rss'),
    )
