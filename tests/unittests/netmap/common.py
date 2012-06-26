import inspect
import os
import unittest
import mock
from nav.models.rrd import RrdDataSource, RrdFile
from nav.web.netmapdev import common
from netmapgraph_testcase import NetmapGraphTestCase

class CommonNetmapTests(NetmapGraphTestCase):

    def setUp(self):
        super(CommonNetmapTests, self).setUp()
        self.path = os.path.dirname(inspect.getfile(inspect.currentframe()))

    def _create_datasources(self):
        self.test_data = []
        for i in xrange(0, 10):
            self.test_data.append(self._create_datasource(i))

    def _create_datasource(self, number):
        rrd_file = RrdFile()
        rrd_file.id = str(number + 200)
        rrd_file.filename = "%s/demo.rrd" % self.path
        rrd_file.value = str(number + 200)
        #rrd_file.netbox

        rrd_datasource = RrdDataSource()
        rrd_datasource.name = "ds" + str(number)
        rrd_datasource.id = str(number + 100)
        rrd_datasource.rrd_file = rrd_file
        rrd_datasource.description = "ifHCInOctets"
        rrd_datasource.type = "DERIVE"
        rrd_datasource.units = "bytes"
        rrd_datasource.threshold = 131072000

        return rrd_datasource

    def test_get_datasource_lookup(self):
        self._create_datasources()
        common._get_datasources = mock.Mock(return_value=self.test_data)

        dict_lookup = common._get_datasource_lookup(self.graph)

        self.assertEquals(len(self.test_data), len(dict_lookup.keys()))
        self.assertEquals('ds8', dict_lookup.get(208)[0].name)
        self.assertTrue(dict_lookup.get('NonExistingValue') is None)


if __name__ == '__main__':
    unittest.main()
