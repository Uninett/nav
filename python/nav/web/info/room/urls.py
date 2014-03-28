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
                                     update_priority, create_csv,
                                     render_sensors, render_deviceinfo)

urlpatterns = patterns('',
    url(r'^$', search, name='room-search'),
    url(r'^(?P<roomid>.+)/netboxes/', render_netboxes,
        name='room-info-netboxes'),
    url(r'^(?P<roomid>.+)/deviceinfo/', render_deviceinfo,
        name='room-info-deviceinfo'),
    url(r'^(?P<roomid>.+)/upload/update_title', update_title,
        name='room-info-update-title'),
    url(r'^(?P<roomid>.+)/upload/delete_image', delete_image,
        name='room-info-delete-image'),
    url(r'^(?P<roomid>.+)/upload/update_priority', update_priority,
        name='room-info-update-priority'),
    url(r'^(?P<roomid>.+)/upload/', upload_image, name='room-info-upload'),
    url(r'^(?P<roomid>.+)/sensors/', render_sensors, name='room-info-sensors'),
    url(r'^(?P<roomid>.+)/$', roominfo, name='room-info'),
    url(r'^csv-download$', create_csv, name='room-csv'),

)
