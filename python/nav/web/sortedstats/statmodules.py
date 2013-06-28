# coding=utf-8
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
"""Contains the modules used for statistics generation"""

import logging
from operator import itemgetter
from urllib import urlencode

from django.core.urlresolvers import reverse

from nav.metrics.data import (get_metric_average, get_metric_max,
                              get_metric_data)
from nav.metrics.lookups import device_reverse

_logger = logging.getLogger(__name__)

# Useful constants
BYTES_TO_BIT = 8.0
TIMETICKS_IN_DAY = 100 * 3600 * 24


class Stat(object):
    """Superclass for statistics generation"""
    title = "Statistics"
    serieslist = None
    data_filter = ''
    graph_filter = None

    def __init__(self, timeframe='-1d', rows=5):
        self.timeframe = timeframe
        self.rows = rows
        self.graph_args = {
            'width': 1046,
            'height': 448,
            'template': 'nav'
        }
        self.scale = None
        self.data = None
        self.graph_url = None
        self.display_data = None

    def collect(self):
        """Collect data"""
        self.data = self.get_sorted_data()
        if self.data:
            self.metric_lookups = self.get_metric_lookups()
            self.graph_url = self.get_graph_url()
            self.display_data = self.get_display_data()

    def get_sorted_data(self):
        """Returns the sorted version of the data"""
        data = self.get_data()
        return self.sort_by_value(data)

    def get_data(self):
        """Gets the relevant data for this statistics"""
        target = self.data_filter.format(serieslist=self.serieslist,
                                         rows=self.rows)
        data = get_metric_average(target, start=self.timeframe)
        if self.scale:
            data = self.upscale(data)
        return data

    def get_metric_lookups(self):
        """Return a mapping of metric -> object"""
        raise NotImplementedError

    def get_graph_url(self):
        """Gets the graph url to display the statistics as a graph"""
        graph_series = self.get_graph_series()

        kwargs = {'serieslist': graph_series}
        if self.scale is not None:
            kwargs['scale'] = "%.20f" % self.scale
        target = self.graph_filter.format(**kwargs)
        self.graph_args['target'] = target
        self.graph_args['from'] = self.timeframe

        return self.create_graph_url()

    def create_graph_url(self):
        """Create url for getting a graph from Graphite"""
        return reverse("graphite-render") + "?" + urlencode(self.graph_args,
                                                            True)

    def get_display_data(self):
        """Gets the human readable version of the raw data"""
        display_data = []
        for key, value in self.data:
            display_data.append((self.metric_lookups[key],
                                 self.humanize(value)))
        return display_data

    def get_graph_series(self):
        """Returns the graph series usable for graphites group function"""
        return ",".join(self.get_graph_metrics())

    def get_graph_metrics(self):
        """Returns the metrics we use for graphing"""
        return [x[0] for x in self.data]

    def upscale(self, data):
        """Upscale data with scale"""
        upscaled = {}
        for key, value in data.items():
            upscaled[key] = value * self.scale
        return upscaled

    @staticmethod
    def sort_by_value(data):
        """Sort dictionary by value"""
        return sorted(data.items(), key=itemgetter(1), reverse=True)

    @staticmethod
    def humanize(number, precision=1):
        """Create human readable version of a number"""
        lookup = (
            (10 ** 9, 'G'),
            (10 ** 6, 'M'),
            (10 ** 3, 'k'),
            (10 ** 0, ''),
            (10 ** -3, 'm'),
            (10 ** -6, 'µ'),
            (10 ** -9, 'n'),
        )
        factor = 1
        suffix = ''
        if number != 0:
            for factor, suffix in lookup:
                if number >= factor:
                    break
        return '%.*f %s' % (precision, number / factor, suffix)


class StatMinFreeAddresses(Stat):
    """Generates statistics for prefixes with high fill levels"""
    title = "Prefix utilization"
    netsize_to_skip = 16

    def __init__(self, *args, **kwargs):
        super(StatMinFreeAddresses, self).__init__(*args, **kwargs)
        self.graph_args['title'] = "Prefix utilization (size > /28)"
        self.graph_args['vtitle'] = "percent"

    def get_data(self):
        targets = self.get_targets()
        target = "highestAverage(group(%s), %s)" % (",".join(targets),
                                                    self.rows)
        data = get_metric_average(target, start=self.timeframe)
        return data

    def get_targets(self):
        """Queries for prefixes that has a ip-range > than netsize_to_skip"""
        data = get_metric_data(
            'maximumAbove(nav.prefixes.*.ip_range, %s)' % self.netsize_to_skip,
            self.timeframe)
        targets = []
        for datapoint in data:
            metric = datapoint['target']
            targets.append('asPercent(%s, %s)' % (
                metric.replace('ip_range', 'ip_count'), metric))
        return targets

    def get_graph_url(self):
        targets = [x[0] for x in self.data]

        self.graph_args['target'] = ["substr(%s,2,3)" % x for x in targets]
        self.graph_args['from'] = self.timeframe

        return self.create_graph_url()


class StatCpuAverage(Stat):
    """Generates statistics for the CPU view"""
    title = 'CPU Highest Average'
    data_filter = 'highestAverage({serieslist}, {rows})'
    graph_filter = 'substr(group({serieslist}),2,3)'
    serieslist = 'nav.devices.*.cpu.*.loadavg5min'

    def __init__(self, *args, **kwargs):
        super(StatCpuAverage, self).__init__(*args, **kwargs)
        self.graph_args['title'] = 'Routers with highest average cpu load'
        self.graph_args['vtitle'] = 'Percent'

    def get_metric_lookups(self):
        return device_reverse(self.get_graph_metrics())


class StatUptime(Stat):
    """Generates statistics for the Uptime view"""
    title = "Highest uptime"
    data_filter = 'highestMax({serieslist}, {rows})'
    graph_filter = 'substr(scale(group({serieslist}), {scale}), 2,3)'
    serieslist = 'nav.devices.*.system.sysuptime'

    def __init__(self, *args, **kwargs):
        super(StatUptime, self).__init__(*args, **kwargs)
        self.scale = 1.0 / TIMETICKS_IN_DAY
        self.graph_args['title'] = 'Network devices with highest uptime'
        self.graph_args['vtitle'] = 'Days'

    def get_data(self):
        target = self.data_filter.format(serieslist=self.serieslist,
                                         rows=self.rows)
        data = get_metric_max(target, start=self.timeframe)
        data = self.upscale(data)
        return data


class StatIfOctets(Stat):
    """Generates statistics for the Octets views"""
    data_filter = 'substr(highestAverage(scaleToSeconds(' \
                  'nonNegativeDerivative({serieslist}),1), {rows}), 0)'
    graph_filter = 'substr(scale(nonNegativeDerivative(scaleToSeconds(group(' \
                   '{serieslist}),1)),{scale}),2,5)'

    def __init__(self, *args, **kwargs):
        super(StatIfOctets, self).__init__(*args, **kwargs)
        self.scale = BYTES_TO_BIT
        self.graph_args['vtitle'] = 'bit/s'

    @staticmethod
    def get_metric_display_name(metric):
        parts = metric.split('.')
        return "%s - %s" % (parts[2], parts[4])


class StatIfInOctets(StatIfOctets):
    """Generates statistics for the Ifinoctets view"""
    title = 'Most traffic in to interface'
    serieslist = 'nav.devices.*.ports.*.ifInOctets'

    def __init__(self, *args, **kwargs):
        super(StatIfInOctets, self).__init__(*args, **kwargs)
        self.graph_args['title'] = 'Interfaces with most average traffic in'


class StatIfOutOctets(StatIfOctets):
    """Generates statistics for the ifoutoctets view"""
    title = 'Most traffic out of interface'
    serieslist = 'nav.devices.*.ports.*.ifOutOctets'

    def __init__(self, *args, **kwargs):
        super(StatIfOutOctets, self).__init__(*args, **kwargs)
        self.graph_args['title'] = 'Interfaces with most average traffic out'


class StatIfErrors(Stat):
    """Generates statistics for all the error views"""
    data_filter = ('substr(highestAverage(scaleToSeconds('
                   'nonNegativeDerivative({serieslist}),1),{rows}),0)')
    graph_filter = ('substr(scaleToSeconds(nonNegativeDerivative('
                    'group({serieslist})),1), 2, 5)')

    def __init__(self, *args, **kwargs):
        super(StatIfErrors, self).__init__(*args, **kwargs)
        self.graph_args['vtitle'] = 'Errors/s'

    def get_data(self):
        target = self.data_filter.format(serieslist=self.serieslist,
                                         rows=self.rows)
        data = get_metric_average(target, start=self.timeframe)
        return data

    @staticmethod
    def get_metric_display_name(metric):
        parts = metric.split('.')
        return "%s - %s" % (parts[2], parts[4])


class StatIfOutErrors(StatIfErrors):
    """Generates statistics for the ifouterrors view"""
    title = 'Most errors on traffic out of interface'
    serieslist = 'nav.devices.*.ports.*.ifOutErrors'

    def __init__(self, *args, **kwargs):
        super(StatIfOutErrors, self).__init__(*args, **kwargs)
        self.graph_args['title'] = 'Interfaces with most errors on traffic out'


class StatIfInErrors(StatIfErrors):
    """Generates statistics for the ifinerrors view"""
    title = 'Most errors on traffic in to interface'
    serieslist = 'nav.devices.*.ports.*.ifInErrors'

    def __init__(self, *args, **kwargs):
        super(StatIfInErrors, self).__init__(*args, **kwargs)
        self.graph_args['title'] = 'Interfaces with most errors on traffic in'
