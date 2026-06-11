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
from nav.topology.stats import NullStats

from nav.models.manage import Interface, Netbox


_logger = logging.getLogger(__name__)


@transaction.atomic()
def update_layer2_topology(links, stats=None):
    """Updates the layer 2 topology in the NAV database.

    :param links: a list of edges from an adjacency graph
    :param stats: optional `ReducerStats` collector for per-run instrumentation.

    """
    stats = stats or NullStats()

    stats.save["links_proposed"] = len(links)

    with stats.time_phase("save.update"):
        for source, dest in links:
            _update_interface_topology(source, dest, stats=stats)

    touched_ifc_ids = [source[1] for source, _dest in links]
    with stats.time_phase("save.clear_nontouched"):
        _clear_topology_for_nontouched(touched_ifc_ids, stats=stats)
    with stats.time_phase("save.clear_mismatched_state"):
        _clear_topology_for_mismatched_state_links(stats=stats)


def _update_interface_topology(source_node, dest_node, stats=None):
    """Updates topology information for the source_node Interface.

    The interface's topology will _only_ be updated if its netbox is up, it is
    administratively up, is not missing, and its current topology information
    differs from what we want to set it to.

    """
    stats = stats or NullStats()

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
    updated = ifc.update(**kwargs)
    stats.save["rows_actually_updated"] += updated


def _clear_topology_for_nontouched(touched_ifc_ids, stats=None):
    """Clears topology information for all interfaces that are administratively
    up, except for those in the touched_ifc_ids list and those who currently
    have no associated topology information.

    """
    stats = stats or NullStats()

    up_or_disabled = Q(ifoperstatus=Interface.OPER_UP) | Q(
        ifadminstatus=Interface.ADM_DOWN
    )
    up_or_disabled_ifcs = Interface.objects.filter(
        up_or_disabled, netbox__up=Netbox.UP_UP
    )
    nontouched_ifcs = up_or_disabled_ifcs.exclude(id__in=touched_ifc_ids)
    clearable_ifcs = nontouched_ifcs.exclude(to_netbox__isnull=True)
    cleared = clearable_ifcs.update(to_netbox=None, to_interface=None)
    stats.save["cleared_nontouched"] += cleared


def _clear_topology_for_mismatched_state_links(stats=None):
    """
    Clears topology for all interfaces that are down, but where the link
    partner is still up.

    This is a clear indication that the topology for an Interface has gone
    stale.
    """
    stats = stats or NullStats()

    mismatched = Interface.objects.filter(
        ifoperstatus=Interface.OPER_DOWN,
        to_interface__ifoperstatus=Interface.OPER_UP,
    )
    count = mismatched.count()
    if count > 0:
        _logger.debug("deleting stale topology for %d operDown interfaces", count)
    mismatched.update(to_netbox=None, to_interface=None)
    stats.save["cleared_mismatched_state"] += count
