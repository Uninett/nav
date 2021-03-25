#!/usr/bin/env python

"""Tests for prefix_ip_collector"""

import unittest
from datetime import datetime
from nav.activeipcollector.manager import find_range, get_timestamp


class TestPrefixIpCollector(unittest.TestCase):
    def test_find_range(self):
        self.assertEqual(find_range('129.241.1.0/24'), 254)
        self.assertEqual(find_range('129.241.1.1'), 0)
        self.assertEqual(find_range('2001:700:0:251e::/64'), 0)

    def test_find_timestamp(self):
        ts = datetime(2012, 10, 4, 14, 30)
        self.assertEqual(get_timestamp(ts), 1349353800)
