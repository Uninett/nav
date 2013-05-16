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
"""Module comment"""

from django.conf.urls import patterns, include, url
from . import (list_navlets, get_user_navlets, add_user_navlet,
               remove_user_navlet, dispatcher, save_navlet_order)

urlpatterns = patterns('',
    url(r'^list-navlets/', list_navlets, name='list-navlets'),
    url(r'^get-user-navlets/', get_user_navlets, name='get-user-navlets'),
    url(r'^add-user-navlet/', add_user_navlet, name='add-user-navlet'),
    url(r'^remove-user-navlet/', remove_user_navlet,
        name='remove-user-navlet'),
    url(r'^get_user_navlet/(?P<navlet_id>\d+)', dispatcher,
        name='get-user-navlet'),
    url(r'^save-navlet-order', save_navlet_order, name='save-navlet-order'),

)
