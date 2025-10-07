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

from django.urls import include, path

from nav.web.info.views import image_help_modal, index, index_search_preview

urlpatterns = [
    path('', index, name="info-search"),
    path('search-preview/', index_search_preview, name="info-search-preview"),
    path('room/', include('nav.web.info.room.urls')),
    path('location/', include('nav.web.info.location.urls')),
    path('vlan/', include('nav.web.info.vlan.urls')),
    path('prefix/', include('nav.web.info.prefix.urls')),
    path('devicegroup/', include('nav.web.info.netboxgroup.urls')),
    path('image/', include('nav.web.info.images.urls')),
    path('event/', include('nav.web.info.event.urls')),
    path('image-help-modal/', image_help_modal, name='info-image-help-modal'),
]
