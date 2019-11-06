#
# Copyright (C) 2013 Uninett AS
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
# License along with NAV. If not, see <http://www.gnu.org/licenses/>
#
"""Machinetracker navlet"""

from django.shortcuts import redirect

from nav.util import IPRange
from nav.django.utils import reverse_with_query as query
from nav.web.navlets import Navlet
from nav.macaddress import MacAddress


def is_ip_address(thing):
    """Checks if this is an ip-address valid for machinetracker"""
    try:
        IPRange.from_string(thing)
    except ValueError:
        return False
    else:
        return True


def is_mac_address(thing):
    """Checks if this is a mac address"""
    try:
        MacAddress(thing)
    except ValueError:
        return False
    else:
        return True


class MachineTrackerNavlet(Navlet):
    """Controller for machinetracker navlet"""

    title = "Machine Tracker"
    description = "Searches in Machine Tracker"

    def get_template_basename(self):
        return "machinetracker"

    def post(self, request):
        """POST controller"""
        return self.redirect_to_machinetracker(request)

    @staticmethod
    def redirect_to_machinetracker(request):
        """Redirects to machinetracker with given forminput"""
        forminput = request.POST.get("from_ip")
        days = int(request.POST.get("days", 7))
        dns = request.POST.get("dns", "")

        if is_ip_address(forminput):
            url = query("machinetracker-ip", ip_range=forminput, days=days, dns=dns)
        elif is_mac_address(forminput):
            url = query("machinetracker-mac", mac=forminput, days=days, dns=dns)
        elif forminput:
            url = query("machinetracker-netbios", search=forminput, days=days)
        else:
            url = query("machinetracker")

        return redirect(url)
