#
# Copyright (C) 2014 Uninett AS
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
"""URL mapping for the various API versions"""

from django.urls import path
from django.urls import include

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from nav.web.api.v1 import urls as v1_urls
from nav.web.api.v2 import urls as v2_urls

# The double-mount of v1 (at /api/ and /api/1/) is de-duplicated by the
# public_schema_filter preprocessing hook configured in SPECTACULAR_SETTINGS.
urlpatterns = [
    path(
        'schema/',
        SpectacularAPIView.as_view(),
        name='schema',
    ),
    path(
        'schema/swagger-ui/',
        SpectacularSwaggerView.as_view(url_name='api:schema'),
        name='swagger-ui',
    ),
    path(
        'schema/redoc/',
        SpectacularRedocView.as_view(url_name='api:schema'),
        name='redoc',
    ),
    path('', include((v1_urls, 'api'))),
    path('1/', include((v1_urls, 'api'), namespace='1')),
    path('2/', include((v2_urls, 'api'), namespace='2')),
]
