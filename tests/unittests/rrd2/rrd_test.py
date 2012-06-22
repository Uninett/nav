import unittest
import subprocess

from django.core.files.storage import FileSystemStorage
from presenter_testcase import PresenterTestCase

class RrdTests(PresenterTestCase):
    """A collection of unit tests testing the Rrd functionality in a Presenter"""

    def setUp(self):
        super(RrdTests, self).setUp()

        filesystem = FileSystemStorage(location=self.path)
        if not filesystem.exists('demo.rrd'):
            self._setup_rrd_file(path)
            print "[i] created demo.rrd architecture dependent dependency for "\
                  "unit tests based on %s/rrd.xml" % path


    def _setup_rrd_file(self, path):
        process = subprocess.Popen(['rrdtool','restore', path+'/rrd.xml',path+'/demo.rrd'])
        process.communicate()[0]
        if  process.returncode!=0:
            raise ValueError("OBS OBS creating rrd file didn't go as planned!")


    def test_read_average(self):
        self.presentation.add_datasource(self.test_data[0])
        result = self.presentation.average()
        self.assertEquals(1, len(result))

        self.assertEquals(list, type(result))

        expected_average = 0
        self.assertEquals(expected_average, result[0])

    def test_read_max(self):
        self.presentation.add_datasource(datasource=self.test_data[0])
        result = self.presentation.max()

        self.assertEquals(0, result)




if __name__ == '__main__':
    unittest.main()
