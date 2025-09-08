#
# Copyright (C) 2013 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Module comment"""

from django.urls import re_path, path
from . import (
    get_user_navlets,
    add_user_navlet,
    add_user_navlet_graph,
    add_navlet_modal,
    remove_user_navlet,
    remove_user_navlet_modal,
    dispatcher,
    save_navlet_order,
    render_base_template,
    set_navlet_preferences,
    add_user_navlet_sensor,
)


urlpatterns = [
    path('get-user-navlets/', get_user_navlets, name='get-user-navlets'),
    path(
        'get-user-navlets/<int:dashboard_id>/',
        get_user_navlets,
        name='get-user-navlets',
    ),
    path('add-user-navlet/', add_user_navlet, name='add-user-navlet'),
    path(
        'add-user-navlet/<int:dashboard_id>/',
        add_user_navlet,
        name='add-user-navlet',
    ),
    path(
        'add-navlet-modal/<int:dashboard_id>/',
        add_navlet_modal,
        name='add-navlet-modal',
    ),
    path('add-user-navlet/graph/', add_user_navlet_graph, name='add-user-navlet-graph'),
    path(
        'add-user-navlet/sensor/',
        add_user_navlet_sensor,
        name='add-user-navlet-sensor',
    ),
    # XXX: wrong regexp in all of these?
    re_path(r'^remove-user-navlet/', remove_user_navlet, name='remove-user-navlet'),
    re_path(
        r'^remove-user-navlet-modal/(?P<navlet_id>\d+)',
        remove_user_navlet_modal,
        name='remove-user-navlet-modal',
    ),
    re_path(r'^get-user-navlet/(?P<navlet_id>\d+)', dispatcher, name='get-user-navlet'),
    re_path(r'^save-navlet-order', save_navlet_order, name='save-navlet-order'),
    re_path(
        r'^navlet-base-template/', render_base_template, name='navlet-base-template'
    ),
    re_path(
        r'^set-navlet-preferences',
        set_navlet_preferences,
        name='set-navlet-preferences',
    ),
]
