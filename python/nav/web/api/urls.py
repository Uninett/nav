#
# Copyright (C) 2014 Uninett AS
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

from django.urls import re_path, include
from nav.web.api.v1 import urls as v1_urls

urlpatterns = [
    re_path(r'^', include((v1_urls, 'api'))),
    re_path(r'^1/', include((v1_urls, 'api'), namespace='1')),
]
