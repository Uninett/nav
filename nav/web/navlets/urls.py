#
# Copyright (C) 2013 Uninett AS
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
"""Module comment"""

from django.conf.urls import url
from . import (get_user_navlets, add_user_navlet,
               add_user_navlet_graph, remove_user_navlet, dispatcher,
               save_navlet_order, render_base_template, set_navlet_preferences,
               add_user_navlet_sensor)


urlpatterns = [
    url(r'^get-user-navlets/$', get_user_navlets,
        name='get-user-navlets'),
    url(r'^get-user-navlets/(?P<dashboard_id>\d+)/$', get_user_navlets,
        name='get-user-navlets'),
    url(r'^add-user-navlet/$', add_user_navlet,
        name='add-user-navlet'),
    url(r'^add-user-navlet/(?P<dashboard_id>\d+)/$', add_user_navlet,
        name='add-user-navlet'),
    url(r'^add-user-navlet/graph/$', add_user_navlet_graph,
        name='add-user-navlet-graph'),
    url(r'^add-user-navlet/sensor/$', add_user_navlet_sensor,
        name='add-user-navlet-sensor'),
    url(r'^remove-user-navlet/', remove_user_navlet,
        name='remove-user-navlet'),
    url(r'^get-user-navlet/(?P<navlet_id>\d+)', dispatcher,
        name='get-user-navlet'),
    url(r'^save-navlet-order', save_navlet_order,
        name='save-navlet-order'),
    url(r'^navlet-base-template/', render_base_template,
        name='navlet-base-template'),
    url(r'^set-navlet-preferences', set_navlet_preferences,
        name='set-navlet-preferences'),
]
