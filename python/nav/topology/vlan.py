#
# Copyright (C) 2011-2015, 2017, 2018 Uninett AS
# Copyright (C) 2018 Uninett AS
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
"""Analysis of VLAN topology as subset of layer 2 topology"""

from collections import defaultdict
from itertools import groupby, chain
import logging
from operator import attrgetter

import networkx as nx
from IPy import IP

from django.db.models import Q
from django.db import transaction

from nav.models.manage import (
    GwPortPrefix,
    Interface,
    SwPortVlan,
    SwPortBlocked,
    Prefix,
    Vlan,
)

from nav.netmap import stubs

_logger = logging.getLogger(__name__)
NO_TRUNK = Q(trunk=False) | Q(trunk__isnull=True)


class VlanGraphAnalyzer(object):
    """Analyzes VLAN topologies as a subset of the layer 2 topology"""

    def __init__(self):
        self.routed_vlans = self._build_vlan_router_dict()
        self.unrouted_vlans = self._build_unrouted_vlan_seed_dict()
        self.layer2 = build_layer2_graph()
        self.stp_blocked = get_stp_blocked_ports()
        _logger.debug("blocked ports: %r", self.stp_blocked)
        self.ifc_vlan_map = {}

    @staticmethod
    def _build_vlan_router_dict():
        """Builds a dictionary of {vlan: GwPortPrefix} mappings.

        For each VLAN, and IPv4 address is preferred over an IPv6 address,
        and lower addresses are preferred over higher ones.

        """

        def _sortkey(gwp):
            ip = IP(gwp.gw_ip)
            return ip.version(), ip

        addrs = sorted(get_active_addresses_of_routed_vlans(), key=_sortkey)
        return dict((addr.prefix.vlan, addr) for addr in reversed(addrs))

    def _build_unrouted_vlan_seed_dict(self):
        return {
            x
            for x in Vlan.objects.filter(
                prefixes__isnull=True, netbox__isnull=False
            ).iterator()
        }

    def analyze_all(self):
        """Analyze all VLAN topologies"""
        for vlan in sorted(self.routed_vlans, key=lambda x: x.vlan):
            _logger.debug("Analyzing routed VLAN %s", vlan)
            self.analyze_vlan(vlan)
        while self.unrouted_vlans:
            vlan = min(self.unrouted_vlans, key=_unrouted_vlan_sort)
            self.unrouted_vlans.remove(vlan)
            if vlan.netbox not in self.layer2:
                continue
            _logger.debug("Analyzing unrouted VLAN %s", vlan)
            self.analyze_vlan(vlan)
        return self.ifc_vlan_map

    def analyze_vlans_by_id(self, vlans):
        """Analyzes a list of VLANs by their PVIDs"""
        vlan_id_map = {vlan.vlan: vlan for vlan in self.routed_vlans.keys()}
        vlan_id_map.update({vlan.vlan: vlan for vlan in self.unrouted_vlans})
        for vlan in vlans:
            if vlan in vlan_id_map:
                self.analyze_vlan(vlan_id_map[vlan])

    def analyze_vlan(self, vlan):
        """Analyzes a single vlan"""
        if vlan in self.routed_vlans:
            addr = self.routed_vlans[vlan]
            analyzer = RoutedVlanTopologyAnalyzer(addr, self.layer2, self.stp_blocked)
        else:
            seed_netbox = vlan.netbox
            analyzer = UnroutedVlanTopologyAnalyzer(
                vlan, seed_netbox, self.layer2, self.stp_blocked
            )
        topology = analyzer.analyze()
        self._integrate_vlan_topology(vlan, topology)
        self._prune_unrouted_vlans(vlan, topology)

    def _prune_unrouted_vlans(self, vlan, topology):
        for ifc in topology:
            for cand in list(self.unrouted_vlans):
                if cand.vlan == vlan.vlan and cand.netbox == ifc.netbox:
                    _logger.debug("pruning vlan %s because of %s", cand, vlan)
                    self.unrouted_vlans.remove(cand)

    def _integrate_vlan_topology(self, vlan, topology):
        for ifc, direction in topology.items():
            if ifc not in self.ifc_vlan_map:
                self.ifc_vlan_map[ifc] = {}
            self.ifc_vlan_map[ifc][vlan] = direction

    def add_access_port_vlans(self):
        """Detects and adds Vlan entries for access ports to the ifc_vlan_map"""
        access_vlan_map = dict(self.find_access_port_vlans())
        self.ifc_vlan_map.update(access_vlan_map)
        return self.ifc_vlan_map

    def find_access_port_vlans(self):
        """Finds and yields the vlans of access ports.

        After the analyze_all step, the ifc_vlan_map will normally only
        contain vlans for uplink/downlink ports, not access ports.  This
        method will find the actual vlan objects of each of the switch access
        ports and yield those as tuples: (interface, {vlan: 'down'}).  These
        can be made into a dictionary suitable for updating ifc_vlan_map.

        """
        groups = groupby(self.ifc_vlan_map, lambda ifc: ifc.netbox)
        for netbox, ifcs in groups:
            for result in self._find_netbox_access_vlans(netbox, list(ifcs)):
                yield result

    def _find_netbox_access_vlans(self, netbox, ifcs):
        vlans = chain(*(self.ifc_vlan_map[ifc].keys() for ifc in ifcs))
        active_vlans = dict((vlan.vlan, vlan) for vlan in vlans)

        access_ifcs = (
            netbox.interfaces.filter(vlan__isnull=False)
            .filter(NO_TRUNK)
            .exclude(id__in=(ifc.id for ifc in ifcs))
        )
        for ifc in access_ifcs:
            if ifc.vlan in active_vlans:
                yield ifc, {active_vlans[ifc.vlan]: 'down'}


class RoutedVlanTopologyAnalyzer(object):
    """Analyzer of a single routed VLAN topology"""

    def __init__(self, address, layer2_graph, stp_blocked=None):
        """Initializes an analyzer for a given routed VLAN.

        :param address: A GwPortPrefix representing the router address of this
                        VLAN.
        :param layer2_graph: A layer 2 graph, as produced by the
                             build_layer2_graph() function.

        """
        self.address = address
        self.layer2 = layer2_graph

        self.vlan = address.prefix.vlan
        self.router_port = address.interface
        self.router = self.router_port.netbox

        self.stp_blocked = stp_blocked or {}
        self.ifc_directions = {}
        self.edge_directions = {}

    def analyze(self):
        """Runs the analysis on the associdated VLAN"""
        if self.router in self.layer2:
            if not self.router_port.to_netbox:
                # likely a GSW, descend on its switch ports by faking an edge
                start_edge = (self.router, self.router, None)
            else:
                start_edge = (self.router, self.router_port.to_netbox, self.router_port)
            self._examine_edge(start_edge)

        return self.ifc_directions

    def _examine_edge(self, edge, visited_nodes=None):
        source, dest, ifc = edge

        visited_nodes = visited_nodes or set()
        is_visited_before = dest in visited_nodes
        if (source, dest) in self.edge_directions:
            direction = self.edge_directions[(source, dest)]
        else:
            direction = 'up' if is_visited_before else 'down'
            self.edge_directions[(source, dest)] = direction
        visited_nodes.add(dest)

        vlan_is_active = (
            direction == 'up'
            and self._vlan_is_active_on_reverse_edge(edge, visited_nodes)
        ) or self._is_vlan_active_on_destination(dest, ifc)

        if direction == 'down' and not is_visited_before:
            # Recursive depth first search on each outgoing edge
            for next_edge in self._out_edges_on_vlan(dest):
                if not self._is_blocked_on_any_end(next_edge):
                    self._log_descent(next_edge)
                    sub_active = self._examine_edge(next_edge, visited_nodes)
                    vlan_is_active = vlan_is_active or sub_active
                else:
                    vlan_is_active = False
                    self._mark_both_ends_as_blocked(next_edge)
                    self._log_block(next_edge)

        if vlan_is_active and ifc:
            _logger.debug(
                "(%s) setting %s direction: %s", self.vlan.vlan, ifc, direction
            )
            self.ifc_directions[ifc] = direction

        return vlan_is_active

    def _vlan_is_active_on_reverse_edge(self, edge, visited_nodes):
        _source, dest, ifc = edge
        reverse_edge = self._find_reverse_edge(edge)
        if reverse_edge:
            reverse_ifc = reverse_edge[2]
            been_there = (
                self._interface_has_been_seen_before(reverse_ifc)
                or dest in visited_nodes
            )
            if been_there:
                return self._ifc_has_vlan(ifc)
        return False

    def _find_reverse_edge(self, edge):
        source, dest, ifc = edge
        dest_ifc = ifc.to_interface

        if source in self.layer2[dest]:
            if dest_ifc and dest_ifc in self.layer2[dest][source]:
                return dest, source, dest_ifc
            else:
                # pick first available return edge when any exist
                return dest, source, list(self.layer2[dest][source].keys())[0]

    def _interface_has_been_seen_before(self, ifc):
        return ifc in self.ifc_directions

    def _is_vlan_active_on_destination(self, dest, ifc):
        if not ifc:
            return False

        if not ifc.trunk:
            return self._ifc_has_vlan(ifc)
        else:
            non_trunks_on_vlan = dest.interfaces.filter(vlan=self.vlan.vlan).filter(
                NO_TRUNK
            )
            if ifc.to_interface:
                non_trunks_on_vlan = non_trunks_on_vlan.exclude(id=ifc.to_interface.id)

            return non_trunks_on_vlan.count() > 0

    def _out_edges_on_vlan(self, node):
        return (
            (u, v, w)
            for u, v, w in self.layer2.out_edges(node, keys=True)
            if self._ifc_has_vlan(w)
        )

    def _ifc_has_vlan(self, ifc):
        return ifc.vlan == self.vlan.vlan or self._vlan_allowed_on_trunk(ifc)

    def _vlan_allowed_on_trunk(self, ifc):
        return (
            ifc.trunk
            and getattr(ifc, 'swport_allowed_vlan', None)
            and self.vlan.vlan in ifc.swport_allowed_vlan
        )

    def _is_blocked_on_any_end(self, edge):
        """Returns True if at least one of the edge endpoints are blocked"""
        reverse_edge = self._find_reverse_edge(edge)
        if not reverse_edge:
            _logger.debug("could not find reverse edge for %r", edge)
        return self._is_edge_blocked(edge) or self._is_edge_blocked(reverse_edge)

    def _is_edge_blocked(self, edge):
        if edge:
            _source, _dest, ifc = edge
            return self.vlan.vlan in self.stp_blocked.get(ifc.id, [])
        return False

    def _log_descent(self, next_edge):
        source, dest, ifc = next_edge
        _logger.debug(
            "(%s) descending from %s (%s [%d]) to %s",
            self.vlan.vlan,
            source.sysname,
            ifc.ifname,
            ifc.id,
            dest.sysname,
        )

    def _log_block(self, next_edge):
        source, _dest, source_ifc = next_edge
        reverse_edge = self._find_reverse_edge(next_edge)
        if reverse_edge:
            dest, _source, dest_ifc = reverse_edge
            _logger.info(
                "at least one of %s (%s) <-> %s (%s) is blocked on VLAN %s",
                source.sysname,
                source_ifc.ifname,
                dest.sysname,
                dest_ifc.ifname,
                self.vlan.vlan,
            )
        else:
            _logger.info(
                "%s (%s) is blocked on VLAN %s",
                source.sysname,
                source_ifc.ifname,
                self.vlan.vlan,
            )

    def _mark_both_ends_as_blocked(self, edge):
        _source, _dest, source_ifc = edge
        self.ifc_directions[source_ifc] = 'blocked'
        reverse_edge = self._find_reverse_edge(edge)
        if reverse_edge:
            _dest, _source, dest_ifc = reverse_edge
            self.ifc_directions[dest_ifc] = 'blocked'


class UnroutedVlanTopologyAnalyzer(RoutedVlanTopologyAnalyzer):
    """Analyzer of a single unrouted VLAN topology"""

    def __init__(self, vlan, seed, layer2_graph, stp_blocked=None):
        """Initializes an analyzer for a given unrouted VLAN.

        :param layer2_graph: A layer 2 graph, as produced by the
                             build_layer2_graph() function.

        """
        self.layer2 = layer2_graph
        self.stp_blocked = stp_blocked or {}
        self.ifc_directions = {}
        self.edge_directions = {}
        self.seed_netbox = seed
        self.vlan = vlan

    def analyze(self):
        start_edge = (self.seed_netbox, self.seed_netbox, None)
        self._examine_edge(start_edge)
        return {ifc: 'undefined' for ifc in self.ifc_directions}


class VlanTopologyUpdater(object):
    """Updater of the VLAN topology.

    Usage example:

      >>> a = VlanGraphAnalyzer()
      >>> ifc_vlan_map = a.analyze_all()
      >>> updater = VlanTopologyUpdater(ifc_vlan_map)
      >>> updater()
      >>>

    """

    def __init__(self, ifc_vlan_map):
        """Initializes a vlan topology updater.

        :param ifc_vlan_map: A dictionary mapping interfaces to Vlans and
                             directions; just as returned by a call to
                             VlanGraphAnalyzer.analyze_all().

        """
        self.ifc_vlan_map = ifc_vlan_map

    def __call__(self):
        return self.update()

    @transaction.atomic()
    def update(self):
        """Updates the VLAN topology in the NAV database"""
        for ifc, vlans in self.ifc_vlan_map.items():
            for vlan, dirstr in vlans.items():
                self._update_or_create_new_swportvlan_entry(ifc, vlan, dirstr)
            self._remove_dead_swpvlan_records_for_ifc(ifc)

        self._delete_swportvlans_from_untouched_ifcs()

    @classmethod
    def _update_or_create_new_swportvlan_entry(cls, ifc, vlan, dirstr):
        direction = cls._direction_from_string(dirstr)
        obj, created = SwPortVlan.objects.get_or_create(
            interface=ifc, vlan=vlan, defaults={'direction': direction}
        )
        if not created and obj.direction != direction:
            obj.direction = direction
            obj.save()
        return object

    DIRECTION_MAP = {
        'up': SwPortVlan.DIRECTION_UP,
        'down': SwPortVlan.DIRECTION_DOWN,
        'blocked': SwPortVlan.DIRECTION_BLOCKED,
        'undefined': SwPortVlan.DIRECTION_UNDEFINED,
    }

    @classmethod
    def _direction_from_string(cls, string):
        return (
            cls.DIRECTION_MAP[string]
            if string in cls.DIRECTION_MAP
            else SwPortVlan.DIRECTION_UNDEFINED
        )

    def _remove_dead_swpvlan_records_for_ifc(self, ifc):
        records_for_ifc = SwPortVlan.objects.filter(interface=ifc)
        active_vlans = self.ifc_vlan_map[ifc].keys()
        dead = records_for_ifc.exclude(vlan__in=active_vlans)
        dead.delete()

    def _delete_swportvlans_from_untouched_ifcs(self):
        """Deletes old swportvlan entries that weren't touched by this update"""
        # this can turn into a rather huge, and surprisingly inefficient SQL
        # statement if we let PostgreSQL do all the work, so we calculate the
        # set difference using Python instead
        touched_interfaceids = set(ifc.pk for ifc in self.ifc_vlan_map)
        existing_interfaceids = set(
            SwPortVlan.objects.distinct().values_list('interface__id', flat=True)
        )
        to_delete = existing_interfaceids.difference(touched_interfaceids)
        if to_delete:
            _logger.debug(
                "deleting obsolete swpvlan records for these ifcs: %s", to_delete
            )
            SwPortVlan.objects.filter(interface__id__in=to_delete).delete()


def build_layer2_graph(related_extra=None):
    """Builds a graph representation of the layer 2 topology stored in the NAV
    database.

    :param related_extra Additional selection_related fields

    :returns: A MultiDiGraph of Netbox nodes, edges annotated with Interface
              model objects.

    """
    graph = nx.MultiDiGraph(name="Layer 2 topology")

    select_related = ('netbox', 'to_netbox', 'to_interface')
    if related_extra:
        select_related = select_related + related_extra

    links = Interface.objects.filter(to_netbox__isnull=False).select_related(
        *select_related
    )

    for link in links:
        dest = link.to_interface.netbox if link.to_interface else link.to_netbox
        graph.add_edge(link.netbox, dest, key=link)
    return graph


def build_layer3_graph(related_extra=None):
    """Build a graph representation of the layer 3 topology stored in the NAV
    database.

    :param related_extra Additional selection_related fields

    : returns: A MultiDiGraph of Netbox nodes, edges annotated with Interface
               model objects.
    """
    graph = nx.MultiGraph(name="Layer 3 topology")

    select_related = (
        'interface__netbox',
        'interface__to_netbox',
        'interface__to_interface',
        'interface__to_interface__netbox',
    )
    if related_extra:
        select_related = select_related + related_extra

    prefixes = (
        Prefix.objects.filter(vlan__net_type__in=('link', 'elink', 'core'))
        .extra(
            where=[
                'NOT (family(netaddr) = 4 AND masklen(netaddr) = 32)',
                'NOT (family(netaddr) = 6 AND masklen(netaddr) = 128)',
            ]
        )
        .select_related("vlan__net_type")
    )

    router_ports = GwPortPrefix.objects.filter(
        prefix__in=prefixes, interface__netbox__category__in=('GW', 'GSW')
    ).select_related(*select_related)

    router_ports_prefix_map = defaultdict(list)
    for router_port in router_ports:
        router_ports_prefix_map[router_port.prefix].append(router_port)

    def _add_edge(gwportprefixes_in_prefix):
        """
        Adds connections between netboxes in gwportprefix (fully connected
        network) note: loop/self.loop edges should _NOT_ use this method for
        adding the loop to the graph.
        """
        for this in gwportprefixes_in_prefix:
            for gwpp in gwportprefixes_in_prefix:
                if this is not gwpp:
                    graph.add_edge(this, gwpp, key=this.prefix)

    for prefix in prefixes:
        gwportprefixes = router_ports_prefix_map.get(prefix)
        if gwportprefixes:
            if prefix.vlan.net_type.id == 'elink':
                if len(gwportprefixes) > 1:
                    # Special case, (horrible) check if it's a local loopback
                    # to same netbox.
                    #
                    # d3js force directed doesn't show loopback edges,
                    # but we'll include it in the graph metadata, in case we
                    # fix the visualizing later.

                    # take first GwPortPrefix in list of GwPortPrefixes,
                    # and use as base to check for loop back edges linking to
                    #  the same netbox.
                    gwpp_match = gwportprefixes[0]

                    if [
                        u.interface.netbox == gwpp_match.interface.netbox
                        for u in gwportprefixes
                    ].count(True) >= 2:
                        for u in gwportprefixes:
                            for v in gwportprefixes:
                                if u is not v:
                                    graph.add_edge(u, v, key=prefix)

                    else:
                        # If not, we'll add the edge anyway and log a warning
                        # about topology detector should really not classify
                        # this as an elink. (since we found >1 known gwpp's
                        # in given prefix means it shold be a link or core.)
                        _logger.warning(
                            "Topology error? %s classified as elink, "
                            "we know %s GwPortPrefixes ...",
                            str(prefix),
                            len(gwportprefixes),
                        )
                        _add_edge(gwportprefixes)
                else:
                    fictive_gwportprefix = stubs.GwPortPrefix()
                    fictive_netbox = stubs.Netbox()
                    if gwportprefixes[0].prefix.vlan.net_ident:
                        fictive_netbox.sysname = str(
                            gwportprefixes[0].prefix.vlan.net_ident
                        )
                    else:
                        fictive_netbox.sysname = str(
                            gwportprefixes[0].interface.ifalias
                        )
                    fictive_netbox.category_id = 'elink'
                    fictive_netbox.id = fictive_netbox.sysname

                    fictive_interface = stubs.Interface()
                    fictive_interface.netbox = fictive_netbox
                    fictive_interface.ifname = (
                        "N/A (peer of %s)" % gwportprefixes[0].gw_ip
                    )
                    fictive_interface.speed = None

                    fictive_gwportprefix.interface = fictive_interface
                    fictive_gwportprefix.gw_ip = fictive_netbox.sysname
                    fictive_gwportprefix.prefix = prefix

                    graph.add_edge(gwportprefixes[0], fictive_gwportprefix, key=prefix)

            else:
                _add_edge(gwportprefixes)
    return graph


def get_active_addresses_of_routed_vlans():
    """Gets a single router port address for each routed VLAN.

    :returns: A list of GwPortPrefix objects.

    """
    addrs = get_routed_vlan_addresses().select_related(
        'prefix__vlan', 'interface__netbox'
    )
    return filter_active_router_addresses(addrs)


def filter_active_router_addresses(gwportprefixes):
    """Filters a GwPortPrefix queryset, leaving only active router addresses.

    For any given prefix, if multiple router addresses exist, the lowest IP
    address will be picked.  If the prefix has a virtual address, it will be
    picked instead.

    :param gwportprefixes: A GwPortPrefix QuerySet.
    :returns: A list of GwPortPrefix objects.

    """
    # It is more or less impossible to get Django's ORM to generate the
    # wonderfully complex SQL needed for this, so we do it by hand.
    raddrs = gwportprefixes.order_by('prefix__id', '-virtual', 'gw_ip')
    grouper = groupby(raddrs, attrgetter('prefix_id'))
    return [next(group) for _key, group in grouper]


def get_routed_vlan_addresses():
    """Gets router port addresses for all routed VLANs.

    :returns: A GwPortPrefix QuerySet.

    """
    raddrs = get_router_addresses()
    return raddrs.filter(prefix__vlan__vlan__isnull=False)


def get_router_addresses():
    """Gets all router port addresses.

    :returns: A GwPortPrefix QuerySet.

    """
    return GwPortPrefix.objects.filter(
        interface__netbox__category__id__in=('GW', 'GSW')
    )


def get_stp_blocked_ports():
    """Returns a dictionary of ports in STP blocking mode.

    :returns: A dictionary: {interfaceid: [vlan1, vlan2, ...]}

    """
    blocked = defaultdict(list)
    for block in SwPortBlocked.objects.all():
        blocked[block.interface_id].append(block.vlan)
    return dict(blocked)


def _unrouted_vlan_sort(vlan):
    return vlan.vlan * 10 + (0 if vlan.has_meaningful_net_ident() else 1)
