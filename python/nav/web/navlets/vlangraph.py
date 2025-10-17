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
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Navlet for displaying a graph giving ip count for a vlan"""

import logging

from django.http import HttpResponse

from nav.web.auth.utils import get_account
from nav.models.manage import Vlan
from nav.models.profiles import AccountNavlet
from nav.web.navlets import Navlet, NAVLET_MODE_VIEW, NAVLET_MODE_EDIT
from nav.web.info.vlan.views import get_vlan_graph_url

_logger = logging.getLogger(__name__)


class VlanGraphNavlet(Navlet):
    """Controller for vlangraph navlet"""

    description = "Displays a graph over active ip-addresses on a vlan"
    title = "Vlan Graph"
    is_editable = True
    refresh_interval = 1000 * 60 * 10  # Refresh every 10 minutes
    image_reload = True

    def get_template_basename(self):
        return "vlangraph"

    def get_context_data(self, **kwargs):
        context = super(VlanGraphNavlet, self).get_context_data(**kwargs)

        vlanid = self.preferences['vlanid'] if 'vlanid' in self.preferences else None
        if self.mode == NAVLET_MODE_VIEW and vlanid:
            url = get_vlan_graph_url(vlanid)
            context['graph_url'] = url
        elif self.mode == NAVLET_MODE_EDIT:
            context['vlans'] = Vlan.objects.filter(vlan__isnull=False).order_by('vlan')
            context['vlanid'] = vlanid

        return context

    def post(self, request):
        """Saves user preferences from edit mode"""
        account = get_account(request)
        nid = int(request.POST.get('id'))
        vlanid = int(request.POST.get('vlanid'))

        try:
            Vlan.objects.get(pk=vlanid)
        except Vlan.DoesNotExist:
            return HttpResponse('This vlan does not exist', status=400)
        else:
            account_navlet = AccountNavlet.objects.get(pk=nid, account=account)
            if not account_navlet.preferences:
                account_navlet.preferences = {'vlanid': vlanid}
            else:
                account_navlet.preferences['vlanid'] = vlanid
            account_navlet.save()

        return HttpResponse()
