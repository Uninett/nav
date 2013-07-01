import unittest
import networkx as nx
from topology_testcase import TopologyTestCase


class MultiGraphToUndirectTests(TopologyTestCase):

    def setUp(self):
        self.nav_graph = nx.MultiGraph()
        self._add_edge(self.nav_graph, 'a', 'a1', 'b', 'b1')
        self._add_edge(self.nav_graph, 'b', 'b1', 'a', 'a1')
        self._add_edge(self.nav_graph, 'a', 'a2', 'b', 'b2')
        self._add_edge(self.nav_graph, 'b', 'b2', 'a', 'a2')

    def _setupNetmapGraph(self):
        self.netmap_graph = nx.Graph(self.nav_graph)
        self.metadata_keys_in_nav_graph = set()
        for node, keys, metadata in self.netmap_graph.edges(data=True):
            metadata_from_nav_graph = self.nav_graph.get_edge_data(node, keys).values()
            metadata = {'meta': metadata_from_nav_graph}

            [self.metadata_keys_in_nav_graph.add(x) for x in metadata_from_nav_graph[0].keys()]

            self.netmap_graph.add_edge(node, keys, attr_dict=metadata)

        # remove metadata not stored under 'meta' key.
        # (this because we simply copy/reduce the nav graph with networkx, it
        # keeps the original meta keys for nav's topology graph building)
        for old_meta_to_delete in self.metadata_keys_in_nav_graph:
            for x, y, data_to_delete in self.netmap_graph.edges_iter(data=True):
                del data_to_delete[old_meta_to_delete]



    # This is basically what a standard NAV topology graph looks like...
    # we need to make it unidirectional while keeping attr_dict
    # from all edges

    # [1 / 3]
    def test_nodes_length_of_orignal_graph_consists_with_nav_topology_behavior(self):
        self.assertEquals(2, len(self.nav_graph.nodes()))

    # [2 / 2]
    def test_edges_length_of_orginal_graph_consists_with_nav_topology_behavior(self):
        self.assertEquals(4, len(self.nav_graph.edges()))

    # [3 / 3]
    def test_metadata_edges_length_of_orginal_graph(self):
        self.assertEquals(4, len(self.nav_graph.get_edge_data('a', 'b').values()))


    # netmap graphs tests below

    def test_nodes_length_of_netmap_graph_is_reduced_properly(self):
        self._setupNetmapGraph()
        # two nodes, A and B
        self.assertEquals(2, len(self.netmap_graph.nodes()))

    def test_edges_length_of_netmap_graph_is_reduced_properly(self):
        self._setupNetmapGraph()
        # one drawn LINE between A and B...
        self.assertEquals(1, len(self.netmap_graph.edges()))

    def test_metadata_is_the_same_in_netmap_and_nav_topologies_graphs(self):
        self._setupNetmapGraph()

        # but it should contain 4 links in META which is directional!
        # [a1-b1, b1-a1, a2-b2, b2-a2]
        self.assertEquals(self.nav_graph.get_edge_data('a', 'b').values(),
                          self.netmap_graph.get_edge_data('a', 'b')['meta'])

    def test_netmap_metadata_shows_4_links_for_the_one_edge_between_a__and_b(self):
        self._setupNetmapGraph()
        self.assertEquals(
            {'uplink':
                 {
                     'thiss':
                         {
                             'interface': 'a1', 'netbox': 'a',
                             'netbox_link': '/ipdevinfo/a',
                             'interface_link':
                                 '/ipdevinfo/a/interface=a1'
                         },
                     'other':
                         {
                             'interface': 'b1', 'netbox': 'b',
                             'netbox_link': '/ipdevinfo/b',
                             'interface_link': '/ipdevinfo/b1'
                         }
                 },
             'links': ['a1-b1']
            },
            self.netmap_graph.get_edge_data('a', 'b')['meta'][0])

        self.assertEquals(
            {'uplink':
                 {
                     'thiss':
                         {
                             'interface': 'a2', 'netbox': 'a',
                             'netbox_link': '/ipdevinfo/a',
                             'interface_link':
                                 '/ipdevinfo/a/interface=a2'
                         },
                     'other':
                         {
                             'interface': 'b2', 'netbox': 'b',
                             'netbox_link': '/ipdevinfo/b',
                             'interface_link': '/ipdevinfo/b2'
                         }
                 },
             'links': ['a2-b2']
            },
            self.netmap_graph.get_edge_data('a', 'b')['meta'][1])

        self.assertEquals(
            {'uplink':
                 {
                     'thiss':
                         {
                             'interface': 'b1', 'netbox': 'b',
                             'netbox_link': '/ipdevinfo/b',
                             'interface_link':
                                 '/ipdevinfo/b/interface=b1'
                         },
                     'other':
                         {
                             'interface': 'a1', 'netbox': 'a',
                             'netbox_link': '/ipdevinfo/a',
                             'interface_link': '/ipdevinfo/a1'
                         }
                 },
             'links': ['b1-a1']
            },
            self.netmap_graph.get_edge_data('a', 'b')['meta'][2])

        self.assertEquals(
            {'uplink':
                 {
                     'thiss':
                         {
                             'interface': 'b2', 'netbox': 'b',
                             'netbox_link': '/ipdevinfo/b',
                             'interface_link':
                                 '/ipdevinfo/b/interface=b2'
                         },
                     'other':
                         {
                             'interface': 'a2', 'netbox': 'a',
                             'netbox_link': '/ipdevinfo/a',
                             'interface_link': '/ipdevinfo/a2'
                         }
                 },
             'links': ['b2-a2']
            },
            self.netmap_graph.get_edge_data('a', 'b')['meta'][3])

if __name__ == '__main__':
    unittest.main()