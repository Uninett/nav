#
# Copyright (C) 2011 Uninett AS
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
"""Functions for updating the database's layer 2 topology"""

import logging

from django.db import transaction
from django.db.models import Q

from nav.topology.analyze import Port

from nav.models.manage import Interface, Netbox


_logger = logging.getLogger(__name__)


@transaction.atomic()
def update_layer2_topology(links):
    """Updates the layer 2 topology in the NAV database.

    :param links: a list of edges from an adjacency graph

    """
    for source, dest in links:
        _update_interface_topology(source, dest)

    touched_ifc_ids = [source[1] for source, _dest in links]
    _clear_topology_for_nontouched(touched_ifc_ids)
    _clear_topology_for_mismatched_state_links()


def _update_interface_topology(source_node, dest_node):
    """Updates topology information for the source_node Interface.

    The interface's topology will _only_ be updated if its netbox is up, it is
    administratively up, is not missing, and its current topology information
    differs from what we want to set it to.

    """
    _netboxid, interfaceid = source_node
    ifc = Interface.objects.filter(
        id=interfaceid,
        ifadminstatus=Interface.ADM_UP,
        netbox__up=Netbox.UP_UP,
        gone_since__isnull=True,
    )

    if isinstance(dest_node, Port):
        kwargs = {'to_netbox': int(dest_node[0]), 'to_interface': int(dest_node[1])}
    else:
        kwargs = {'to_netbox': int(dest_node), 'to_interface': None}

    ifc = ifc.exclude(**kwargs)
    ifc.update(**kwargs)


def _clear_topology_for_nontouched(touched_ifc_ids):
    """Clears topology information for all interfaces that are administratively
    up, except for those in the touched_ifc_ids list and those who currently
    have no associated topology information.

    """
    up_or_disabled = Q(ifoperstatus=Interface.OPER_UP) | Q(
        ifadminstatus=Interface.ADM_DOWN
    )
    up_or_disabled_ifcs = Interface.objects.filter(
        up_or_disabled, netbox__up=Netbox.UP_UP
    )
    nontouched_ifcs = up_or_disabled_ifcs.exclude(id__in=touched_ifc_ids)
    clearable_ifcs = nontouched_ifcs.exclude(to_netbox__isnull=True)
    clearable_ifcs.update(to_netbox=None, to_interface=None)


def _clear_topology_for_mismatched_state_links():
    """
    Clears topology for all interfaces that are down, but where the link
    partner is still up.

    This is a clear indication that the topology for an Interface has gone
    stale.
    """
    mismatched = Interface.objects.filter(
        ifoperstatus=Interface.OPER_DOWN,
        to_interface__ifoperstatus=Interface.OPER_UP,
    )
    count = mismatched.count()
    if count > 0:
        _logger.debug("deleting stale topology for %d operDown interfaces", count)
    mismatched.update(to_netbox=None, to_interface=None)
