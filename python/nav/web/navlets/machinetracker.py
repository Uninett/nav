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
# License along with NAV. If not, see <http://www.gnu.org/licenses/>
#
"""Machinetracker navlet"""

from nav.web.navlets import Navlet, NAVLET_MODE_EDIT, NAVLET_MODE_VIEW
from django.shortcuts import redirect


class MachineTrackerNavlet(Navlet):
    """Controller for machinetracker navlet"""

    title = "MachineTracker"
    base = "machinetracker"
    is_editable = True

    def post(self, request):
        return self.redirect_to_machinetracker(request)

    def redirect_to_machinetracker(self, request):
        return redirect('machinetracker-ip_short_search', **{
            'from_ip': request.POST.get('from_ip'),
            'days': int(request.POST.get('days', 7)),
            'dns': request.POST.get('dns', '')
        })
