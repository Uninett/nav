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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Django URL configuration"""


from django.conf.urls.defaults import url, patterns
from nav.web.info.room.views import (search, roominfo, render_netboxes,
                                     upload_image, update_title, delete_image,
                                     update_priority)

urlpatterns = patterns('',
    url(r'^$', search, name='room-search'),
    url(r'^(?P<roomid>.+)/netboxes/', render_netboxes,
        name='room-info-netboxes'),
    url(r'^(?P<roomid>.+)/upload/update_title', update_title,
        name='room-info-update-title'),
    url(r'^(?P<roomid>.+)/upload/delete_image', delete_image,
        name='room-info-update-title'),
    url(r'^(?P<roomid>.+)/upload/update_priority', update_priority,
        name='room-info-update-priority'),
    url(r'^(?P<roomid>.+)/upload/', upload_image, name='room-info-upload'),
    url(r'^(?P<roomid>.+)/$', roominfo, name='room-info'),

)
