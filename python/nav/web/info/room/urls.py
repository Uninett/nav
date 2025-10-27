#
# Copyright (C) 2012 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Django URL configuration"""

from django.urls import path
from django.urls import re_path
from nav.web.info.room import views


urlpatterns = [
    path('', views.search, name='room-search'),
    re_path(
        r'^(?P<roomid>.+)/netboxes/', views.render_netboxes, name='room-info-netboxes'
    ),
    re_path(
        r'^(?P<roomid>.+)/deviceinfo/',
        views.render_deviceinfo,
        name='room-info-deviceinfo',
    ),
    re_path(r'^(?P<roomid>.+)/upload/', views.upload_image, name='room-info-upload'),
    re_path(
        r'^(?P<roomid>.+)/sensors/', views.render_sensors, name='room-info-sensors'
    ),
    path(
        '<str:roomid>/racks/add_rack',
        views.add_rack,
        name='room-info-racks-add-rack',
    ),
    re_path(
        r'^(?P<roomid>.+)/racks/add_rack_modal',
        views.add_rack_modal,
        name='room-info-racks-add-rack-modal',
    ),
    re_path(
        r'^(?P<roomid>.+)/racks/(?P<rackid>\d+)/rename_rack',
        views.rename_rack,
        name='room-info-racks-rename-rack',
    ),
    re_path(
        r'^(?P<roomid>.+)/racks/remove_rack',
        views.remove_rack,
        name='room-info-racks-remove-rack',
    ),
    re_path(
        r'^(?P<roomid>.+)/racks/add_sensor',
        views.render_add_sensor_modal,
        name='room-info-racks-add-sensor-modal',
    ),
    re_path(
        r'^(?P<roomid>.+)/racks/remove_sensor',
        views.remove_sensor,
        name='room-info-racks-remove-sensor',
    ),
    re_path(
        r'^(?P<roomid>.+)/racks/save_sensor_order',
        views.save_sensor_order,
        name='room-info-racks-save-sensor-order',
    ),
    re_path(
        r'^(?P<roomid>.+)/racks/save_rack_order',
        views.save_rack_order,
        name='room-info-racks-save-rack-order',
    ),
    re_path(
        r'^(?P<roomid>.+)/racks/save_rack_color',
        views.save_rack_color,
        name='room-info-racks-save-rack-color',
    ),
    re_path(
        r'^(?P<roomid>.+)/racks/save_sensor',
        views.save_sensor,
        name='room-info-racks-save-sensor',
    ),
    re_path(r'^(?P<roomid>.+)/racks/', views.render_racks, name='room-info-racks'),
    path('<str:roomid>/', views.roominfo, name='room-info'),
    path('csv-download', views.create_csv, name='room-csv'),
    path(
        'aboutthesearch',
        views.render_about_the_search_modal,
        name='room-info-about-the-search',
    ),
]
