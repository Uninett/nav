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
"""Contains the class for the PortAdmin navlet"""
from django.shortcuts import redirect

from nav.models.manage import Netbox
from nav.util import is_valid_ip
from nav.web.navlets import Navlet


class PortadminNavlet(Navlet):
    """The PortAdmin navlet"""

    title = 'PortAdmin'
    description = 'Navlet for searching in Portadmin'

    def get_template_basename(self):
        return "portadmin"

    def post(self, request):
        search = request.POST.get('searchvalue')
        if is_valid_ip(search):
            return redirect('portadmin-ip', kwargs={'ip': search})
        else:
            try:
                netboxes = Netbox.objects.filter(sysname__istartswith=search)
            except Netbox.DoesNotExist:
                pass
            else:
                # Pick the first and best of the results
                return redirect('portadmin-sysname',
                                sysname=netboxes[0].sysname)
