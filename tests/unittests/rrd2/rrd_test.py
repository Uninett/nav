import unittest
import subprocess

from django.core.files.storage import FileSystemStorage
import math
from nav.rrd2 import presenter
from presenter_testcase import PresenterTestCase

class RrdTests(PresenterTestCase):
    """A collection of unit tests testing the Rrd functionality in a Presenter"""

    def setUp(self):
        super(RrdTests, self).setUp()

        filesystem = FileSystemStorage(location=self.path)
        if not filesystem.exists('demo.rrd'):
            self._setup_rrd_file(self.path)
            print "[i] created demo.rrd architecture dependent dependency for "\
                  "unit tests based on %s/rrd.xml" % self.path


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

    def test_read_average_valid_value(self):
        self.presentation = presenter.Presentation(time_frame='year', to_time=self.demo_to_time)
        self.presentation.add_datasource(self.test_data[0])
        result = self.presentation.average()
        self.assertEquals(1, len(result))

        self.assertEquals(list, type(result))

        expected_average = 2372285.2512119999
        self.assertEquals(expected_average, result[0])

    def test_read_max(self):
        self.presentation.add_datasource(datasource=self.test_data[0])
        result = self.presentation.max()
        self.assertTrue(math.isnan(result[0]))

    def test_read_max_valid_value(self):
        self.presentation = presenter.Presentation(time_frame='year', to_time=self.demo_to_time)
        self.presentation.add_datasource(datasource=self.test_data[0])
        result = self.presentation.max()

        expected_max = 11861200.312999999
        self.assertEquals(expected_max, result[0])

    def test_read_min(self):
        self.presentation.add_datasource(datasource=self.test_data[0])
        result = self.presentation.min()

        self.assertTrue(math.isnan(result[0]))


    def test_read_min_valid_value(self):
        self.presentation = presenter.Presentation(time_frame='year', to_time=self.demo_to_time)
        self.presentation.add_datasource(datasource=self.test_data[0])
        result = self.presentation.min()

        expected_min = 902148.62742000003

        self.assertEquals(expected_min, result[0])

    def test_read_sum(self):
        self.presentation.add_datasource(datasource=self.test_data[0])
        result = self.presentation.min()

        self.assertTrue(math.isnan(result[0]))

    def test_read_sum_valid_value(self):
        self.presentation = presenter.Presentation(time_frame='year', to_time=self.demo_to_time)
        self.presentation.add_datasource(datasource=self.test_data[0])
        result = self.presentation.sum()

        expected_sum = 856394975.68765986

        self.assertEquals(expected_sum, result[0])

    def test_valid_points(self):
        self.presentation.add_datasource(datasource=self.test_data[0])
        result = self.presentation.valid_points()

        self.assertEquals(1, len(result[0]))
        self.assertTrue(result[0][0] is None)

    def test_valid_points_valid_value(self):
        self.presentation = presenter.Presentation(time_frame='year', to_time=self.demo_to_time)
        self.presentation.add_datasource(datasource=self.test_data[0])

        result = self.presentation.valid_points()

        self.assertEquals(1, len(result))
        self.assertEquals([[361, 0, 0.0]], result)






if __name__ == '__main__':
    unittest.main()
