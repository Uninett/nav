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
from nav.models.manage import SwPortVlan, Prefix
from nav.netmap.metadata import edge_metadata_layer3, edge_metadata_layer2, \
    node_to_json_layer2
from nav.topology import vlan


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


if __name__ == '__main__':
    import doctest
    print doctest.testmod()


class NetmapEdge(frozenset):
    """ Represents an edge.
    This means   a,b == b,a
    (helps dealing with MultiDiGraph to MultiGraph)
    Note: objects must be hashable!
    run-time: o(n)
    """

    def __eq__(self, other):
        if not isinstance(other, NetmapEdge):
            return False
        return Counter(self) == Counter(other)

    def __ne__(self, other):
        return not self.__eq__(other)

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
    """Builds a dictionary to lookup VLAN (IP broadcast domain) information
     for layer3. See nav.models.manage.Vlan

    :param a networkx NAV topology graph
    :returns a map to lookup prefixes by internal NAV VLAN ID"""

    prefix_list_id = list()
    for _, _, prefix in graph.edges_iter(keys=True):
        prefix_list_id.append(prefix.vlan.id)

    prefixes_by_navvlan = defaultdict(list)
    for prefix_in_navvlan in Prefix.objects.filter(
        vlan__id__in=list(prefix_list_id)).select_related():

        prefixes_by_navvlan[prefix_in_navvlan.vlan.id].append(prefix_in_navvlan)

    return prefixes_by_navvlan

def _convert_to_unidirectional_and_attach_directional_metadata(
        topology_without_metadata, edge_metadata_function, vlan_by_interface):
    """
    Reduces a topology graph from nav.topology.vlan, but retains it's
     directional (MultiDiGraph) properties as metadata under the key 'meta'

    This is done as the visualization in Netmap won't ever be drawing multiple
    spines between edges as it will turn into a mess, instead we want to access
    such data as metadata.

    :param topology_without_metadata: nav.topology.vlan.build*_graph networkx graph
    :param edge_metadata_function layer specific metadata function for edges.
    :param vlan_by_interface: dictionary to lookup up vlan's attached to given interface
    :return: reduced networkx topology graph with directional metadata attached under 'meta'
    """
    _LOGGER.debug(
        "_convert_to_unidirectional_and_attach_directional_metadata()")
    netmap_graph = nx.Graph(topology_without_metadata)
    _LOGGER.debug(
        "_convert_to_unidirectional_and_attach_directional_metadata()"
        " reduce done")

    # set to keep in memory to make sure a1<->b1 edges doesn't count twice (directional).
    # (as we use the original directional nav.topology.vlan directional MultiDiGraph
    # to build and attach metadata at the reduced graph)
    seen_edge = set()

    # basically loops over the whole graph here, make sure we fetch all 'loose'
    # ends and makes sure they get metadata attached.
    for node, neighbors_dict in topology_without_metadata.adjacency_iter():
        for neighbors_node, list_of_linked_interfaces in neighbors_dict\
            .iteritems():
            for interface in list_of_linked_interfaces:
                # fetch existing metadata that might have been added already
                existing_metadata = netmap_graph.get_edge_data(
                    interface.netbox,
                    neighbors_node
                )

                netmap_edge = NetmapEdge((interface, interface.to_interface))
                if netmap_edge in seen_edge:
                    # skips if already proccessed metadata for this edge
                    # (a,b) == (b,a) with NetmapEdge.
                    #
                    # basically helps us do the
                    #   MultiDiGraph to MultiGraph logic
                    continue
                else:
                    seen_edge.add(netmap_edge)
                    if existing_metadata:
                        updated_metadata = existing_metadata.items()
                    else:
                        updated_metadata = {}

                    additional_metadata = edge_metadata_function(
                        interface.netbox,
                        interface,
                        neighbors_node,
                        interface.to_interface,
                        vlan_by_interface
                    )

                    if len(updated_metadata)>1:
                        raise SystemError(
                            "Error while merging existing metadata with new "
                            "metadata while creating netmap topology graph")
                    elif len(updated_metadata)==1:
                        updated_metadata = dict(updated_metadata)[
                            'meta'].append(additional_metadata)
                    else:
                        updated_metadata = {'meta': [additional_metadata]}

                    # create new/updates existing edge with updated metadata.
                    netmap_graph.add_edge(
                        node,
                        neighbors_node,
                        attr_dict=updated_metadata
                    )
    _LOGGER.debug(
        "_convert_to_unidirectional_and_attach_directional_metadata()"
        " all metadata updated")
    return netmap_graph

def build_netmap_layer2_graph(view=None):
    """
    Builds a netmap layer 2 graph, based on nav's build_layer2_graph method.


    :param view A NetMapView for getting node positions according to saved
    netmap view.

    :return NetworkX MultiDiGraph with attached metadata for edges and nodes
            (obs! metadata has direction metadata added!)
    """
    _LOGGER.debug("build_netmap_layer2_graph() start")
    topology_without_metadata = vlan.build_layer2_graph(
        (
        'to_interface__netbox', 'to_interface__netbox__room', 'to_netbox__room',
        'netbox__room', 'to_interface__netbox__room__location',
        'to_netbox__room__location', 'netbox__room__location'))
    _LOGGER.debug("build_netmap_layer2_graph() topology graph done")

    vlan_by_interface, vlan_by_netbox = _get_vlans_map_layer2(
        topology_without_metadata)
    _LOGGER.debug("build_netmap_layer2_graph() vlan mappings done")


    netmap_graph = _convert_to_unidirectional_and_attach_directional_metadata(
        topology_without_metadata,
        edge_metadata_layer2,
        vlan_by_interface
    )

    _LOGGER.debug(
        "build_netmap_layer2_graph() graph reduced and metadata attached done")

    for node, data in netmap_graph.nodes_iter(data=True):
        if vlan_by_netbox.has_key(node):
            data['metadata'] = {
                'vlans': sorted(vlan_by_netbox.get(node).iteritems(),
                    key=lambda x: x[1].vlan.vlan)}
    _LOGGER.debug("build_netmap_layer2_graph() vlan metadata for _nodes_ done")

    if view:
        netmap_graph = _attach_node_positions(netmap_graph,
                                              view.node_position_set.all())
    _LOGGER.debug("build_netmap_layer2_graph() view positions and graph done")
    return netmap_graph


def build_netmap_layer3_graph(view=None):
    """
    Builds a netmap layer 3 graph, based on nav's build_layer3_graph method.


    :param view A NetMapView for getting node positions according to saved
    netmap view.

    :return NetworkX MultiGraph with attached metadata for edges and nodes
            (obs! metadata has direction metadata added!)
    """
    _LOGGER.debug("build_netmap_layer3_graph() start")
    topology_without_metadata = vlan.build_layer3_graph(
        ('prefix__vlan__net_type', 'gwportprefix__prefix__vlan__net_type',))
    _LOGGER.debug("build_netmap_layer3_graph() topology graph done")

    vlans_map = _get_vlans_map_layer3(topology_without_metadata)
    _LOGGER.debug("build_netmap_layer2_graph() vlan mappings done")

    # Make a copy of the graph, and add edge meta data
    graph = nx.MultiGraph()

    for gwpp_a, gwpp_b, prefix in topology_without_metadata.edges_iter(
        keys=True):

        netbox_a = gwpp_a.interface.netbox
        netbox_b = gwpp_b.interface.netbox

        graph.add_edge(netbox_a, netbox_b, key=prefix.vlan.id,
            metadata=edge_metadata_layer3(gwpp_a, gwpp_b,
                vlans_map.get(prefix.vlan.id)))
    _LOGGER.debug("build_netmap_layer3_graph() graph copy with metadata done")

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
    for node in graph.nodes(data=True):
        # Find node metadata in saved map view if it has any.
        node_meta_dict = [x for x in node_set if x.netbox == node[0]]

        # Attached position meta data if map view has meta data on node in graph
        if node_meta_dict:
            if node[1].has_key('metadata'):
                # has vlan meta data, need to just update position data
                node[1]['metadata'].update({'position': node_meta_dict[0]})
            else:
                node[1]['metadata'] = {'position': node_meta_dict[0]}
    return graph


