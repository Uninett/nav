#
# Copyright (C) 2012 UNINETT AS
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
"""netmap's topology functions"""
import logging
import networkx as nx
from collections import defaultdict
from nav.models.manage import SwPortVlan
from nav.netmap.metadata import edge_metadata_layer3, edge_metadata_layer2
from nav.netmap.traffic import get_traffic_data, Traffic


_LOGGER = logging.getLogger(__name__)

from operator import itemgetter
from heapq import nlargest
from itertools import repeat, ifilter

# http://code.activestate.com/recipes/576611/ for python 2.5 and 2.6 until
# NAV requirement specifies python 2.7 and we can use collections.Counter
# License: MIT . Also linked from
# http://docs.python.org/2/library/collections.html#collections.Counter
# todo : NAVs requirements changes to python 2.7, kill this Counter!
class Counter(dict):
    '''Dict subclass for counting hashable objects.  Sometimes called a bag
    or multiset.  Elements are stored as dictionary keys and their counts
    are stored as dictionary values.

    >>> Counter('zyzygy')
    Counter({'y': 3, 'z': 2, 'g': 1})

    '''

    def __init__(self, iterable=None, **kwds):
        '''Create a new, empty Counter object.  And if given, count elements
        from an input iterable.  Or, initialize the count from another mapping
        of elements to their counts.

        >>> c = Counter()                           # a new, empty counter
        >>> c = Counter('gallahad')                 # a new counter from an iterable
        >>> c = Counter({'a': 4, 'b': 2})           # a new counter from a mapping
        >>> c = Counter(a=4, b=2)                   # a new counter from keyword args

        '''
        self.update(iterable, **kwds)

    def __missing__(self, key):
        return 0

    def most_common(self, n=None):
        '''List the n most common elements and their counts from the most
        common to the least.  If n is None, then list all element counts.

        >>> Counter('abracadabra').most_common(3)
        [('a', 5), ('r', 2), ('b', 2)]

        '''
        if n is None:
            return sorted(self.iteritems(), key=itemgetter(1), reverse=True)
        return nlargest(n, self.iteritems(), key=itemgetter(1))

    def elements(self):
        '''Iterator over elements repeating each as many times as its count.

        >>> c = Counter('ABCABC')
        >>> sorted(c.elements())
        ['A', 'A', 'B', 'B', 'C', 'C']

        If an element's count has been set to zero or is a negative number,
        elements() will ignore it.

        '''
        for elem, count in self.iteritems():
            for _ in repeat(None, count):
                yield elem

    # Override dict methods where the meaning changes for Counter objects.

    @classmethod
    def fromkeys(cls, iterable, v=None):
        raise NotImplementedError(
            'Counter.fromkeys() is undefined.  Use Counter(iterable) instead.')

    def update(self, iterable=None, **kwds):
        '''Like dict.update() but add counts instead of replacing them.

        Source can be an iterable, a dictionary, or another Counter instance.

        >>> c = Counter('which')
        >>> c.update('witch')           # add elements from another iterable
        >>> d = Counter('watch')
        >>> c.update(d)                 # add elements from another counter
        >>> c['h']                      # four 'h' in which, witch, and watch
        4

        '''
        if iterable is not None:
            if hasattr(iterable, 'iteritems'):
                if self:
                    self_get = self.get
                    for elem, count in iterable.iteritems():
                        self[elem] = self_get(elem, 0) + count
                else:
                    dict.update(self, iterable) # fast path when counter is empty
            else:
                self_get = self.get
                for elem in iterable:
                    self[elem] = self_get(elem, 0) + 1
        if kwds:
            self.update(kwds)

    def copy(self):
        'Like dict.copy() but returns a Counter instance instead of a dict.'
        return Counter(self)

    def __delitem__(self, elem):
        'Like dict.__delitem__() but does not raise KeyError for missing values.'
        if elem in self:
            dict.__delitem__(self, elem)

    def __repr__(self):
        if not self:
            return '%s()' % self.__class__.__name__
        items = ', '.join(map('%r: %r'.__mod__, self.most_common()))
        return '%s({%s})' % (self.__class__.__name__, items)

    # Multiset-style mathematical operations discussed in:
    #       Knuth TAOCP Volume II section 4.6.3 exercise 19
    #       and at http://en.wikipedia.org/wiki/Multiset
    #
    # Outputs guaranteed to only include positive counts.
    #
    # To strip negative and zero counts, add-in an empty counter:
    #       c += Counter()

    def __add__(self, other):
        '''Add counts from two counters.

        >>> Counter('abbb') + Counter('bcc')
        Counter({'b': 4, 'c': 2, 'a': 1})


        '''
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem in set(self) | set(other):
            newcount = self[elem] + other[elem]
            if newcount > 0:
                result[elem] = newcount
        return result

    def __sub__(self, other):
        ''' Subtract count, but keep only results with positive counts.

        >>> Counter('abbbc') - Counter('bccd')
        Counter({'b': 2, 'a': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem in set(self) | set(other):
            newcount = self[elem] - other[elem]
            if newcount > 0:
                result[elem] = newcount
        return result

    def __or__(self, other):
        '''Union is the maximum of value in either of the input counters.

        >>> Counter('abbb') | Counter('bcc')
        Counter({'b': 3, 'c': 2, 'a': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        _max = max
        result = Counter()
        for elem in set(self) | set(other):
            newcount = _max(self[elem], other[elem])
            if newcount > 0:
                result[elem] = newcount
        return result

    def __and__(self, other):
        ''' Intersection is the minimum of corresponding counts.

        >>> Counter('abbb') & Counter('bcc')
        Counter({'b': 1})

        '''
        if not isinstance(other, Counter):
            return NotImplemented
        _min = min
        result = Counter()
        if len(self) < len(other):
            self, other = other, self
        for elem in ifilter(self.__contains__, other):
            newcount = _min(self[elem], other[elem])
            if newcount > 0:
                result[elem] = newcount
        return result


def _get_vlans_map_layer2(graph):
    """Builds two dictionaries to lookup VLAN information for layer2
    :param a networkx NAV topology graph
    :returns a tuple to look up vlans by interface and/or netbox"""
    interface_id_list = list()
    for _, _, key in graph.edges_iter(keys=True):
        if key.vlan:
            interface_id_list.append(key.id)

    vlan_by_interface = defaultdict(list)
    vlan_by_netbox = defaultdict(dict)
    for swpv in SwPortVlan.objects.filter(
        interface__in=list(interface_id_list)).select_related():

        vlan_by_interface[swpv.interface].append(swpv)

        # unique storing on internal nav vlan id
        vlan_by_netbox[swpv.interface.netbox].update({swpv.vlan.id:swpv})

    return (vlan_by_interface, vlan_by_netbox)

def _get_vlans_map_layer3(graph):
    vlans = set()
    for _, _, swpv in graph.edges_iter(keys=True):
        vlans.add(swpv)
    return vlans


def build_netmap_layer2_graph(topology_without_metadata, vlan_by_interface,
                              vlan_by_netbox, load_traffic=False, view=None):
    """
    Builds a netmap layer 2 graph, based on nav's build_layer2_graph method.
    Reduces a topology graph from nav.topology.vlan, but retains it's
     directional (MultiDiGraph) properties as metadata under the key 'metadata'

    This is done as the visualization in Netmap won't ever be drawing multiple
    spines between edges as it will turn into a mess, instead we want to access
    such data as metadata.

    :param topology_without_metadata: nav.topology.vlan.build*_graph networkx
     graph
    :param vlan_by_interface: dictionary to lookup up vlan's attached to given
     interface
    :param vlan_by_netbox: dictonary to lookup up vlan's, keyed by netbox.
    :param view A NetMapView for getting node positions according to saved
     netmap view.
    :type topology_without_metadata: networkx.MultiDiGraph
    :type vlan_by_interface: dict
    :type vlan_by_netbox: dict
    :type view: nav.modeles.profiles.NetmapView
    :return NetworkX Graph with attached metadata for edges and nodes
    """
    _LOGGER.debug(
        "_build_netmap_layer2_graph()")
    netmap_graph = nx.Graph()

    interfaces = set()

    # basically loops over the whole MultiDiGraph from nav.topology and make
    # sure we fetch all 'loose' ends and makes sure they get attached as
    # metadata into netmap_graph
    for source, neighbors_dict in topology_without_metadata.adjacency_iter():
        for target, connected_interfaces_at_source_for_target in (
            neighbors_dict.iteritems()):
            for interface in connected_interfaces_at_source_for_target:
                # fetch existing metadata that might have been added already
                existing_metadata = netmap_graph.get_edge_data(
                    source,
                    target
                ) or {}
                port_pairs = existing_metadata.setdefault('port_pairs', set())
                port_pair = tuple(
                    sorted(
                        (interface, interface.to_interface),
                        key=lambda
                                interfjes: interfjes and interfjes.pk or None
                    )
                )
                port_pairs.add(port_pair)
                if port_pair[0] is not None:
                    interfaces.add(port_pair[0])
                if port_pair[1] is not None:
                    interfaces.add(port_pair[1])

                netmap_graph.add_edge(source, target,
                                      attr_dict=existing_metadata)

    _LOGGER.debug(
        "build_netmap_layer2_graph() graph reduced.Port_pair metadata attached")

    empty_traffic = Traffic()
    for source, target, metadata_dict in netmap_graph.edges_iter(data=True):
        for interface_a, interface_b in metadata_dict.get('port_pairs'):
            traffic = get_traffic_data(
                (interface_a, interface_b)) if load_traffic else empty_traffic
            additional_metadata = edge_metadata_layer2((source, target),
                                                       interface_a,
                                                       interface_b,
                                                       vlan_by_interface,
                                                       traffic)

            metadata = metadata_dict.setdefault('metadata', list())
            metadata.append(additional_metadata)

    _LOGGER.debug(
        "build_netmap_layer2_graph() netmap metadata built")


    for node, data in netmap_graph.nodes_iter(data=True):
        if node in vlan_by_netbox:
            data['metadata'] = {
                'vlans': sorted(vlan_by_netbox[node].iteritems(),
                    key=lambda x: x[1].vlan.vlan)}
    _LOGGER.debug("build_netmap_layer2_graph() vlan metadata for _nodes_ done")

    if view:
        saved_views = view.node_position_set.all()
        netmap_graph = _attach_node_positions(netmap_graph,
                                              saved_views)
    _LOGGER.debug("build_netmap_layer2_graph() view positions and graph done")

    return netmap_graph


def build_netmap_layer3_graph(topology_without_metadata, load_traffic=False,
                              view=None):
    """
    Builds a netmap layer 3 graph, based on nav's build_layer3_graph method.

    :param load_traffic: set to true for fetching Traffic statistics data
                         for your network topology.
    :param view: A NetMapView for getting node positions according to saved
                 netmap view.
    :type load_traffic: bool
    :type view: nav.models.profiles.NetmapView

    :return NetworkX Graph with attached metadata for edges and nodes
            (obs! metadata has direction metadata added!)
    """

    # Make a copy of the graph, and add edge meta data
    graph = nx.Graph()
    interfaces = set()
    for gwpp_a, gwpp_b, prefix in topology_without_metadata.edges_iter(
        keys=True):

        netbox_a = gwpp_a.interface.netbox
        netbox_b = gwpp_b.interface.netbox

        existing_metadata = graph.get_edge_data(netbox_a, netbox_b) or {}
        gwportprefix_pairs = existing_metadata.setdefault('gwportprefix_pairs',
                                                          set())
        gwportprefix = tuple(
            sorted(
                (gwpp_a, gwpp_b),
                key=lambda
                        gwpprefix: gwpprefix and gwpprefix.gw_ip or None
            )
        )
        gwportprefix_pairs.add(gwportprefix)
        if gwpp_a.interface is not None:
            interfaces.add(gwpp_a.interface)
        if gwpp_b.interface is not None:
            interfaces.add(gwpp_b.interface)

        graph.add_edge(netbox_a, netbox_b, key=prefix.vlan,
            attr_dict=existing_metadata)
    _LOGGER.debug("build_netmap_layer3_graph() graph copy with metadata done")

    empty_traffic = Traffic()
    for source, target, metadata_dict in graph.edges_iter(data=True):
        for gwpp_a, gwpp_b in metadata_dict.get('gwportprefix_pairs'):
            traffic = get_traffic_data(
                (gwpp_a.interface, gwpp_b.interface)
            ) if load_traffic else empty_traffic
            additional_metadata = edge_metadata_layer3((source, target),
                                                       gwpp_a,
                                                       gwpp_b,
                                                       traffic)
            assert gwpp_a.prefix.vlan.id == gwpp_b.prefix.vlan.id, (
                "GwPortPrefix must reside inside VLan for given Prefix, "
                "bailing!")
            metadata = metadata_dict.setdefault('metadata', defaultdict(list))
            metadata[gwpp_a.prefix.vlan.id].append(additional_metadata)


    if view:
        graph = _attach_node_positions(graph, view.node_position_set.all())
    _LOGGER.debug("build_netmap_layer3_graph() view positions and graph done")
    return graph


def _attach_node_positions(graph, node_set):
    """ Attaches node positions from a set of nodes which is extracted from a
    given map view earlier in the call stack.

    :param graph graph to modify metadata on
    :param node_set NetmapViewNodePosition collection for a given map view
    """

    # node is a tuple(netbox, networkx_graph_node_meta_dict)
    # Traversing our generated graph which misses node positions..
    for node, metadata in graph.nodes(data=True):
        # Find node metadata in saved map view if it has any.
        node_meta_dict = [x for x in node_set if x.netbox == node]

        # Attached position meta data if map view has meta data on node in graph
        if node_meta_dict:
            if metadata.has_key('metadata'):
                # has vlan meta data, need to just update position data
                metadata['metadata'].update({'position': node_meta_dict[0]})
            else:
                metadata['metadata'] = {'position': node_meta_dict[0]}
    return graph


