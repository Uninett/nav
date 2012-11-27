#!/usr/bin/env python

"""Tests for prefix_ip_collector"""

import unittest
from datetime import datetime
from nav.activeipcollector.manager import (find_range, convert_to_filename,
                                           get_timestamp)

class TestPrefixIpCollector(unittest.TestCase):

    def test_find_range(self):
        self.assertEqual(find_range('129.241.1.0/24'), 254)
        self.assertEqual(find_range('129.241.1.1'), 0)
        self.assertEqual(find_range('2001:700:0:251e::/64'), 0)


    def test_convert_to_filename(self):
        self.assertEqual(convert_to_filename('129.241.1.0/24'),
                         '129_241_1_0_24.rrd')
        self.assertEqual(convert_to_filename('2001:700:0:500::15/128'),
                         '2001_700_0_500__15_128.rrd')

    def test_find_timestamp(self):
        ts = datetime(2012, 10, 04, 14, 32)
        self.assertEqual(get_timestamp(ts), 1349353800)
        ts = datetime(2012, 10, 04, 14, 28)
        self.assertEqual(get_timestamp(ts), 1349353800)

