#
# Copyright (C) 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Module comment"""

import unittest
import sys
from nav.navrrd2whisper import (get_rras, calculate_time_periods,
                                calculate_retentions, get_datasources,
                                create_whisper_path,
                                calculate_absolute_from_rate,
                                insert_missing_values, find_meta)


class NavRrd2WhisperTest(unittest.TestCase):

    def setUp(self):
        self.rrd_info = {'ds[ip_count].index': 0L,
                         'ds[ip_count].last_ds': '2',
                         'ds[ip_count].max': 100000.0,
                         'ds[ip_count].min': 0.0,
                         'ds[ip_count].minimal_heartbeat': 3600L,
                         'ds[ip_count].type': 'GAUGE',
                         'ds[ip_count].unknown_sec': 0L,
                         'ds[ip_count].value': 0.0,
                         'ds[ip_range].index': 2L,
                         'ds[ip_range].last_ds': '2',
                         'ds[ip_range].max': 100000.0,
                         'ds[ip_range].min': 0.0,
                         'ds[ip_range].minimal_heartbeat': 3600L,
                         'ds[ip_range].type': 'GAUGE',
                         'ds[ip_range].unknown_sec': 0L,
                         'ds[ip_range].value': 0.0,
                         'ds[mac_count].index': 1L,
                         'ds[mac_count].last_ds': '2',
                         'ds[mac_count].max': 100000.0,
                         'ds[mac_count].min': 0.0,
                         'ds[mac_count].minimal_heartbeat': 3600L,
                         'ds[mac_count].type': 'GAUGE',
                         'ds[mac_count].unknown_sec': 0L,
                         'ds[mac_count].value': 0.0,
                         'filename': '128_39_255_112_30.rrd',
                         'header_size': 3048L,
                         'last_update': 1370503800L,
                         'rra[0].cdp_prep[0].unknown_datapoints': 0L,
                         'rra[0].cdp_prep[0].value': None,
                         'rra[0].cdp_prep[1].unknown_datapoints': 0L,
                         'rra[0].cdp_prep[1].value': None,
                         'rra[0].cdp_prep[2].unknown_datapoints': 0L,
                         'rra[0].cdp_prep[2].value': None,
                         'rra[0].cf': 'AVERAGE',
                         'rra[0].cur_row': 444L,
                         'rra[0].pdp_per_row': 1L,
                         'rra[0].rows': 600L,
                         'rra[0].xff': 0.5,
                         'rra[1].cdp_prep[0].unknown_datapoints': 0L,
                         'rra[1].cdp_prep[0].value': 6.0,
                         'rra[1].cdp_prep[1].unknown_datapoints': 0L,
                         'rra[1].cdp_prep[1].value': 6.0,
                         'rra[1].cdp_prep[2].unknown_datapoints': 0L,
                         'rra[1].cdp_prep[2].value': 6.0,
                         'rra[1].cf': 'AVERAGE',
                         'rra[1].cur_row': 62L,
                         'rra[1].pdp_per_row': 6L,
                         'rra[1].rows': 600L,
                         'rra[1].xff': 0.5,
                         'rra[2].cdp_prep[0].unknown_datapoints': 0L,
                         'rra[2].cdp_prep[0].value': 30.0,
                         'rra[2].cdp_prep[1].unknown_datapoints': 0L,
                         'rra[2].cdp_prep[1].value': 30.0,
                         'rra[2].cdp_prep[2].unknown_datapoints': 0L,
                         'rra[2].cdp_prep[2].value': 30.0,
                         'rra[2].cf': 'AVERAGE',
                         'rra[2].cur_row': 520L,
                         'rra[2].pdp_per_row': 24L,
                         'rra[2].rows': 600L,
                         'rra[2].xff': 0.5,
                         'rra[3].cdp_prep[0].unknown_datapoints': 0L,
                         'rra[3].cdp_prep[0].value': 2.0,
                         'rra[3].cdp_prep[1].unknown_datapoints': 0L,
                         'rra[3].cdp_prep[1].value': 2.0,
                         'rra[3].cdp_prep[2].unknown_datapoints': 0L,
                         'rra[3].cdp_prep[2].value': 2.0,
                         'rra[3].cf': 'MAX',
                         'rra[3].cur_row': 436L,
                         'rra[3].pdp_per_row': 24L,
                         'rra[3].rows': 600L,
                         'rra[3].xff': 0.5,
                         'rra[4].cdp_prep[0].unknown_datapoints': 0L,
                         'rra[4].cdp_prep[0].value': 30.0,
                         'rra[4].cdp_prep[1].unknown_datapoints': 0L,
                         'rra[4].cdp_prep[1].value': 30.0,
                         'rra[4].cdp_prep[2].unknown_datapoints': 0L,
                         'rra[4].cdp_prep[2].value': 30.0,
                         'rra[4].cf': 'AVERAGE',
                         'rra[4].cur_row': 588L,
                         'rra[4].pdp_per_row': 96L,
                         'rra[4].rows': 600L,
                         'rra[4].xff': 0.5,
                         'rra[5].cdp_prep[0].unknown_datapoints': 0L,
                         'rra[5].cdp_prep[0].value': 2.0,
                         'rra[5].cdp_prep[1].unknown_datapoints': 0L,
                         'rra[5].cdp_prep[1].value': 2.0,
                         'rra[5].cdp_prep[2].unknown_datapoints': 0L,
                         'rra[5].cdp_prep[2].value': 2.0,
                         'rra[5].cf': 'MAX',
                         'rra[5].cur_row': 423L,
                         'rra[5].pdp_per_row': 96L,
                         'rra[5].rows': 600L,
                         'rra[5].xff': 0.5,
                         'rrd_version': '0003',
                         'step': 1800L}
        self.seconds_per_point = self.rrd_info['step']
        self.last_update = self.rrd_info['last_update']
        self.rras = False

    def get_cached_rras(self):
        if not self.rras:
            self.rras = get_rras(self.rrd_info)
        return self.rras

    def test_datasources(self):
        datasources = get_datasources(self.rrd_info)
        names = [x.name for x in datasources]
        types = [x.type for x in datasources]
        self.assertEqual(sorted(['ip_count', 'ip_range', 'mac_count']),
                         sorted(names))
        self.assertEqual(['GAUGE'] * 3, types)

    def test_rras_length(self):
        rras = self.get_cached_rras()
        self.assertEqual(len(rras), 4)

    def test_rra_content(self):
        rra = self.get_cached_rras()[3]
        self.assertEqual(rra.cf, 'AVERAGE')
        self.assertEqual(rra.pdp_per_row, 96)
        self.assertEqual(rra.rows, 600)

    def test_one_period_per_rra(self):
        rras = self.get_cached_rras()
        periods = calculate_time_periods(rras, self.seconds_per_point,
                                         self.last_update)
        self.assertEqual(len(periods), len(rras))

    def test_start_time_should_be_less_than_end_time(self):
        periods = calculate_time_periods(self.get_cached_rras(),
                                         self.seconds_per_point,
                                         self.last_update)
        for period in periods:
            self.assertTrue(period.start_time < period.end_time)

    def test_first_period_length(self):
        periods = calculate_time_periods(self.get_cached_rras(),
                                         self.seconds_per_point,
                                         self.last_update)
        length = int(periods[0][1]) - int(periods[0][0])
        self.assertEqual(length, self.seconds_per_point * 600)

    def test_retentions(self):
        retentions = calculate_retentions(self.get_cached_rras(),
                                          self.seconds_per_point)
        fasit = [(1800, 600), (10800, 600), (43200, 600), (172800, 600)]
        self.assertEqual(retentions, fasit)

    def test_rate_conversion(self):
        interval = 300
        rates = [200, 200, 200]
        self.assertEqual(calculate_absolute_from_rate(rates, interval),
                         [60000, 120000, 180000])

    def test_rate_is_none(self):
        interval = 300
        rates = [200, None, 200]
        self.assertEqual(calculate_absolute_from_rate(rates, interval),
                         [60000, None, 60000])

    def test_insert_missing_values(self):
        values = [1, 2, 3]
        num_missing = 3
        modified = insert_missing_values(values, num_missing)
        self.assertEqual(modified, [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3])

    def test_get_meta_port(self):
        meta = {
            '^nav\..*ports\..*': {
                'aggregationMethod': 'last'
            }
        }
        self.assertEqual(
            find_meta(
                'nav.devices.blaasal-sw_uninett_no.ports.Gi2_46.ifInOctets'),
            meta['^nav\..*ports\..*'])

    def test_get_meta_count(self):
        meta = {
            '^nav\..*-count$': {
                'xFilesFactor': 0,
                'aggregationMethod': 'sum'
            }
        }
        self.assertEqual(
            find_meta(
                'nav.devices.blaasal-sw_uninett_no.blapp.something-count'),
            meta['^nav\..*-count$'])

