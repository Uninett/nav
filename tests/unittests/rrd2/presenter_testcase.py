import inspect
import os
import unittest
from nav.models.rrd import RrdFile, RrdDataSource
from nav.rrd2 import presenter

class PresenterTestCase(unittest.TestCase):

    def setUp(self):
        self.presentation = presenter.Presentation()

        self.path = os.path.dirname(inspect.getfile(inspect.currentframe()))

        self.test_data = []
        for i in xrange(0, 10):
            self.test_data.append(self._create_datasource(i))

    def _create_datasource(self, number):
        rrd_file = RrdFile()
        rrd_file.id = str(number + 200)
        rrd_file.filename = "%s/demo.rrd" % self.path

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