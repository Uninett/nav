#
# Copyright (C) 2011, 2012 Uninett AS
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
"""Diff stored and current topology"""

from nav.models.manage import Interface

from .analyze import (
    AdjacencyReducer,
    build_candidate_graph_from_db,
    get_aggregate_mapping,
)
from .analyze import Box, Port


def printdiffs():
    """Test a live reduction and output a comparison of the stored topology
    and the currently detected one.

    """
    cand = build_candidate_graph_from_db()
    aggregates = get_aggregate_mapping(include_stacks=True)
    reducer = AdjacencyReducer(cand, aggregates)
    reducer.reduce()

    connections = reducer.get_single_edges_from_ports()

    ifcs = Interface.objects.select_related('netbox', 'to_netbox', 'to_interface')

    saved_links = ifcs.filter(to_netbox__isnull=False)
    saved_links = dict((link.id, link) for link in saved_links)

    found_links = dict((u[1], v) for u, v in connections)
    found_link_ids = set(found_links)

    new_link_ids = found_link_ids.difference(saved_links)
    new_links = ifcs.filter(id__in=new_link_ids)
    new_links = dict((link.id, link) for link in new_links)

    deleted_link_ids = set(saved_links).difference(found_link_ids)
    deleted_links = ifcs.filter(id__in=deleted_link_ids)
    deleted_links = {link.id: link for link in deleted_links}

    output = []
    for port_id in found_link_ids.union(new_links).union(deleted_links):
        if port_id in found_links and port_id in saved_links:
            port = saved_links[port_id]
            found_link = found_links[port_id]

            diff = False
            if isinstance(found_link, Box) and port.to_netbox.id != found_link:
                diff = True
            elif isinstance(found_link, Port) and (
                port.to_netbox.id != found_link[0]
                or not port.to_interface
                or port.to_interface.id != found_link[1]
            ):
                diff = True
            if diff:
                output.append(
                    "%s (%s): %s%s -> %s"
                    % (
                        port.netbox.sysname,
                        port.ifname,
                        port.to_netbox.sysname,
                        (
                            (" (%s)" % port.to_interface.ifname)
                            if port.to_interface
                            else ''
                        ),
                        found_link,
                    )
                )

        elif port_id in new_links:
            port = new_links[port_id]
            found_link = found_links[port_id]

            output.append(
                "%s (%s): no link -> %s"
                % (port.netbox.sysname, port.ifname, found_link)
            )

        elif port_id in saved_links and port_id not in found_links:
            port = saved_links[port_id]
            output.append(
                "%s (%s): %s%s -> no link"
                % (
                    port.netbox.sysname,
                    port.ifname,
                    port.to_netbox.sysname,
                    ((" (%s)" % port.to_interface.ifname) if port.to_interface else ''),
                )
            )

    output.sort()
    print('\n'.join(output))


if __name__ == '__main__':
    printdiffs()
