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
"""Navlet for displaying an ip count for a vlan"""
import logging
from django.shortcuts import redirect

from nav.django.utils import get_account
from nav.models.profiles import AccountNavlet
from nav.web.navlets import Navlet
from nav.web.info.vlan.views import create_vlan_graph
_logger = logging.getLogger(__name__)


class VlanGraphNavlet(Navlet):
    """Controller for vlangraphnavlet"""

    description = "Displays a graph over active ip-addresses on a vlan"
    base = "vlangraph"
    title = "Vlan Graph"
    is_editable = True

    def get_context_data(self, **kwargs):
        context = super(VlanGraphNavlet, self).get_context_data(**kwargs)

        navlet_id = int(self.request.GET.get('id'))
        account = get_account(self.request)
        account_navlet = AccountNavlet.objects.get(pk=navlet_id,
                                                   account=account)

        if self.preferences:
            graph = create_vlan_graph(account_navlet.options['vlanid'])
            context['graph_url'] = graph.get_url()
            context['vlanid'] = self.preferences['vlanid']

        return context

    def post(self, request):
        """Saves user preferences from edit mode"""
        account = get_account(request)
        nid = int(request.POST.get('id'))
        vlanid = int(request.POST.get('vlanid'))

        account_navlet = AccountNavlet.objects.get(pk=nid, account=account)
        account_navlet.preferences = {'vlanid': vlanid}
        account_navlet.save()

        return redirect('webfront-index')
