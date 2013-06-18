
import unittest
import re
from mock import Mock, patch
from nav.rrd2.presenter import Graph, time_last

class TestGraph(unittest.TestCase):

    def setUp(self):
        with patch('nav.config.read_flat_config'):
            self.graph = Graph()
            self.datasource = Mock()
            self.datasource.id = 1
            self.datasource.rrd_file.get_file_path = Mock(
                return_value='/usr/local/nav/rrd/activeip/blapp.rrd')
            self.datasource.name = 'activeip'

    def test_init(self):
        self.assertEqual(self.graph.args, [])
        self.assertEqual(self.graph.opts['-s'], 'now-1d')
        self.assertEqual(self.graph.opts['-e'], 'now')

    def test_time_last(self):
        self.assertEqual(time_last('now'), 'now-1d')
        self.assertEqual(time_last('now', 'hour'), 'now-1h')
        self.assertEqual(time_last('now', 'hour', 2), 'now-2h')

    def test_add_argument(self):
        self.graph.add_argument("test")
        self.assertEqual(self.graph.args, ["test"])
        self.graph.add_argument("test2")
        self.assertEqual(self.graph.args, ["test", "test2"])

    def test_add_option(self):
        self.graph.add_option({'-s': 'now-1y'})
        self.assertEqual(self.graph.opts['-s'], 'now-1y')
        self.graph.add_option({'-blapp': 'blupp'})
        self.assertEqual(self.graph.opts['-blapp'], 'blupp')

    def test_get_color(self):
        self.assertEqual(self.graph.colorindex, 0)
        self.graph._get_color()
        self.assertEqual(self.graph.colorindex, 1)

    def test_get_color_overflow(self):
        self.graph.colorindex = 20
        self.graph._get_color()
        self.assertEqual(self.graph.colorindex, 0)

    def test_add_datasource(self):
        self.graph.add_datasource(self.datasource)
        self.assertEqual(self.graph.args, [
            'DEF:id1=/usr/local/nav/rrd/activeip/blapp.rrd:activeip:AVERAGE',
            'LINE1:id1#00cc00'])
