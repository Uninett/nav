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
from nav.web.navlets import Navlet
from nav.web.info.vlan.views import create_vlan_graph
_logger = logging.getLogger(__name__)

class VlanGraphNavlet(Navlet):
    """Controller for vlangraphnavlet"""

    description = "Displays a graph over active ip-addresses on a vlan"
    base = "vlangraph"
    title = "Vlan Graph"

    def get_context_data(self, **kwargs):
        context = super(VlanGraphNavlet, self).get_context_data(**kwargs)
        graph = create_vlan_graph(322)
        _logger.error(graph.get_url())
        context['graph_url'] = graph.get_url()
        return context
