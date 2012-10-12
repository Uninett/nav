#
# Copyright (C) 2012 (SD -311000) UNINETT AS
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
"""Urlconfig for arnold"""

from django.conf.urls.defaults import patterns, url
from nav.web.arnold.views import (render_history, render_detained_ports,
                                  render_search, render_justifications)

urlpatterns = patterns('',
   url(r"^$", render_detained_ports, name="arnold_index"),
   url(r"^history/$", render_history, name="arnold-history"),
   url(r"^detainedports/$", render_detained_ports, name="arnold-detainedports"),
   url(r"^search/$", render_search, name="arnold-search"),
   url(r"^addreason/$", render_justifications, name="arnold-justificatons"),
   url(r"^addreason/edit/(?P<jid>\d+)$", render_justifications, name="arnold-justificatons-edit"),
)

