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
        self.downtime1 = self.alert1.end_time - self.alert1.start_time
        self.downtime2 = self.alert2.end_time - self.alert2.start_time
        self.alerts = [self.alert1, self.alert2]

    def test_zero_downtime(self):
        start = datetime(2014, 2, 1)
        end = datetime(2014, 2, 27)
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
