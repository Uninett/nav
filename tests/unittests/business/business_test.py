"""Basic tests for nav.arnold"""
# pylint: disable=C0111
import unittest
from datetime import datetime, timedelta

from nav.web.business import utils
from nav.models.event import AlertHistory


class TestBusinessUtils(unittest.TestCase):
    """Tests for nav.arnold"""

    def setUp(self):
        self.alert1 = AlertHistory(start_time=datetime(2014, 1, 1),
                                   end_time=datetime(2014, 1, 3))
        self.alert2 = AlertHistory(start_time=datetime(2014, 1, 20),
                                   end_time=datetime(2014, 1, 21))
        self.maintenance0 = AlertHistory(start_time=datetime(2013, 12, 31),
                                         end_time=datetime(2014, 1, 1))
        self.maintenance1 = AlertHistory(start_time=datetime(2014, 1, 2),
                                         end_time=datetime(2014, 1, 5))
        self.maintenance2 = AlertHistory(start_time=datetime(2014, 1, 7),
                                         end_time=datetime(2014, 1, 13))
        self.maintenance3 = AlertHistory(start_time=datetime(2014, 1, 15),
                                         end_time=datetime(2014, 1, 21))
        self.maintenance5 = AlertHistory(start_time=datetime(2014, 1, 29),
                                         end_time=datetime(2014, 2, 2))
        self.downtime1 = self.alert1.end_time - self.alert1.start_time
        self.downtime2 = self.alert2.end_time - self.alert2.start_time
        self.alerts = [self.alert1, self.alert2]

    def test_zero_downtime(self):
        start = datetime(2014, 2, 1)
        end = datetime(2014, 2, 27)
        downtime = utils.compute_downtime(self.alerts, start, end)
        self.assertEqual(downtime, timedelta(0))

    def test_zero_downtime2(self):
        start = datetime(2014, 1, 4)
        end = datetime(2014, 1, 10)
        downtime = utils.compute_downtime(self.alerts, start, end)
        self.assertEqual(downtime, timedelta(0))


    def test_single_downtime(self):
        start = datetime(2014, 1, 1)
        end = datetime(2014, 1, 31)
        downtime = utils.compute_downtime([self.alert1], start, end)
        self.assertEqual(downtime, self.downtime1)

    def test_multiple_downtimes(self):
        start = datetime(2014, 1, 1)
        end = datetime(2014, 1, 31)
        downtime = utils.compute_downtime(self.alerts, start, end)
        self.assertEqual(downtime, self.downtime1 + self.downtime2)

    def test_full_availability(self):
        start = datetime(2014, 2, 1)
        end = datetime(2014, 2, 27)
        interval = end - start
        avail = utils.compute_availability(timedelta(0), interval)
        self.assertEqual(avail, 100)

    def test_no_availability(self):
        start = datetime(2014, 2, 1)
        end = datetime(2014, 2, 2)
        interval = end - start
        avail = utils.compute_availability(timedelta(days=1), interval)
        self.assertEqual(avail, 0)

    def test_find_intervals_one_maintenance(self):
        start = datetime(2014, 1, 1)
        end = datetime(2014, 1, 31)
        intervals = utils.find_intervals(start, end, [self.maintenance1])
        self.assertEqual(len(intervals), 2)
        a, b = intervals
        self.assertEqual(a, (start, self.maintenance1.start_time))
        self.assertEqual(b, (self.maintenance1.end_time, end))

    def test_find_intervals_two_maintenances(self):
        start = datetime(2014, 1, 1)
        end = datetime(2014, 1, 31)
        intervals = utils.find_intervals(start, end, [self.maintenance1, self.maintenance2])
        self.assertEqual(len(intervals), 3)
        a, b, c = intervals
        self.assertEqual(a, (start, self.maintenance1.start_time))
        self.assertEqual(b, (self.maintenance1.end_time, self.maintenance2.start_time))
        self.assertEqual(c, (self.maintenance2.end_time, end))

    def test_find_intervals_three_maintenances(self):
        start = datetime(2014, 1, 1)
        end = datetime(2014, 1, 31)
        intervals = utils.find_intervals(start, end, [self.maintenance1, self.maintenance2, self.maintenance3])
        self.assertEqual(len(intervals), 4)
        a, b, c, d = intervals
        self.assertEqual(a, (start, self.maintenance1.start_time))
        self.assertEqual(b, (self.maintenance1.end_time, self.maintenance2.start_time))
        self.assertEqual(c, (self.maintenance2.end_time, self.maintenance3.start_time))
        self.assertEqual(d, (self.maintenance3.end_time, end))

    def test_find_interval_overlapping_start(self):
        start = datetime(2014, 1, 1)
        end = datetime(2014, 1, 31)
        intervals = utils.find_intervals(start, end, [self.maintenance0])
        self.assertEqual(len(intervals), 1)
        a, = intervals
        self.assertEqual(a, (self.maintenance0.end_time, end))

    def test_find_interval_overlapping_end(self):
        start = datetime(2014, 1, 1)
        end = datetime(2014, 1, 31)
        intervals = utils.find_intervals(start, end, [self.maintenance5])
        self.assertEqual(len(intervals), 1)
        a, = intervals
        self.assertEqual(a, (start, self.maintenance5.start_time))

    def test_find_interval_cover_all(self):
        """Test the case where:

        - the maintenance starts before the start
        - the maintenance ends after the end
        """
        maintenance = AlertHistory(start_time=datetime(2013, 1, 29),
                                   end_time=datetime(9999, 12, 31))
        start = datetime(2014, 1, 1)
        end = datetime(2014, 1, 31)
        intervals = utils.find_intervals(start, end, [maintenance])
        self.assertEqual(len(intervals), 0)

    def test_find_interval_combined(self):
        start = datetime(2014, 1, 1)
        end = datetime(2014, 1, 31)
        intervals = utils.find_intervals(start, end, [
            self.maintenance0, self.maintenance1, self.maintenance2, self.maintenance5])
        self.assertEqual(len(intervals), 3)
        a, b, c = intervals
        self.assertEqual(a, (self.maintenance0.end_time, self.maintenance1.start_time))
        self.assertEqual(b, (self.maintenance1.end_time, self.maintenance2.start_time))
        self.assertEqual(c, (self.maintenance2.end_time, self.maintenance5.start_time))
