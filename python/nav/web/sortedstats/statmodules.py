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

from operator import itemgetter
from urllib import urlencode

from django.core.urlresolvers import reverse

from nav.metrics.data import get_metric_average, get_metric_max


# Useful constants
BYTES_TO_MBIT = 8.0 / (1024 * 1024)
TIMETICKS_IN_DAY = 100 * 3600 * 24


class Stat(object):
    """Superclass for statistics generation"""
    serieslist = None
    data_filter = None
    graph_filter = None
    graph_args = None
    default_graph_args = {
        'width': 1046,
        'height': 448,
        'template': 'nav'
    }
    scale = None

    def __init__(self, timeframe='-1d', rows=5):
        self.timeframe = timeframe
        self.rows = rows
        self.data = self.get_sorted_data()
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
        return get_metric_average(target, start=self.timeframe)

    def get_graph_url(self):
        """Gets the graph url to display the statistics as a graph"""
        graph_series = self.get_graph_series()

        kwargs = {'serieslist': graph_series}
        if self.scale is not None:
            kwargs['scale'] = "%.20f" % self.scale
        target = self.graph_filter.format(**kwargs)
        args = self.dict_merge(self.graph_args, {'target': target,
                                                 'from': self.timeframe})
        return self.create_graph_url(args)

    def get_display_data(self):
        """Gets the human readable version of the raw data"""
        display_data = []
        for key, value in self.data:
            display_data.append((self.get_metric_display_name(key), value))
        return display_data

    @staticmethod
    def get_metric_display_name(metric):
        """Return the display name for the metric"""
        return metric.split('.')[2]

    def create_graph_url(self, args):
        """Create url for getting a graph from Graphite"""
        graph_args = self.dict_merge(self.default_graph_args, args)
        return reverse("graphite-render") + "?" + urlencode(graph_args)

    def get_graph_series(self):
        """Returns the graph series usable for graphites group function"""
        return ",".join([x[0] for x in self.data])

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
    def dict_merge(a_dict, b_dict):
        """Merge two dictionaries. b will overwrite a"""
        return dict(a_dict.items() + b_dict.items())


class StatCpuAverage(Stat):
    """Generates statistics for the CPU view"""
    title = 'CPU Highest Average'
    graph_args = {
        'title': 'Routers with highest average cpu load',
        'vtitle': 'Percent'
    }
    data_filter = 'highestAverage({serieslist}, {rows})'
    graph_filter = 'substr(group({serieslist}),2,3)'
    serieslist = 'nav.devices.*.cpu.*.loadavg5min'


class StatUptime(Stat):
    """Generates statistics for the Uptime view"""
    title = "Highest uptime"
    data_filter = 'highestMax({serieslist}, {rows})'
    graph_filter = 'substr(scale(group({serieslist}), {scale}), 2,3)'
    serieslist = 'nav.devices.*.system.sysuptime'
    graph_args = {
        'title': 'Network devices with highest uptime',
        'vtitle': 'Days'
    }
    scale = 1.0 / TIMETICKS_IN_DAY

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
    graph_filter = 'substr(scale(nonNegativeDerivative(scaleToSeconds(' \
                   'group({serieslist}),1)),{scale}),2,5)'
    scale = BYTES_TO_MBIT

    @staticmethod
    def get_metric_display_name(metric):
        parts = metric.split('.')
        return "%s - %s" % (parts[2], parts[4])


class StatIfInOctets(StatIfOctets):
    """Generates statistics for the Ifinoctets view"""
    title = 'Most traffic in to interface'
    serieslist = 'nav.devices.*.ports.*.ifInOctets'
    graph_args = {
        'title': 'Interfaces with most average traffic in',
        'vtitle': 'Mbit',
        'yUnitSystem': 'binary'
    }


class StatIfOutOctets(StatIfOctets):
    """Generates statistics for the ifoutoctets view"""
    title = 'Most traffic out of interface'
    serieslist = 'nav.devices.*.ports.*.ifOutOctets'
    scale = BYTES_TO_MBIT
    graph_args = {
        'title': 'Interfaces with most average traffic out',
        'vtitle': 'Mbit',
        'yUnitSystem': 'binary'
    }


class StatIfErrors(Stat):
    """Generates statistics for all the error views"""
    data_filter = 'highestAverage({serieslist}, {rows})'
    graph_filter = 'substr(group({serieslist}), 2, 5)'

    @staticmethod
    def get_metric_display_name(metric):
        parts = metric.split('.')
        return "%s - %s" % (parts[2], parts[4])


class StatIfOutErrors(StatIfErrors):
    """Generates statistics for the ifouterrors view"""
    title = 'Most errors on traffic out of interface'
    serieslist = 'nav.devices.*.ports.*.ifOutErrors'
    graph_args = {
        'title': 'Interfaces with most errors on traffic out',
        'vtitle': 'Errors',
    }


class StatIfInErrors(StatIfErrors):
    """Generates statistics for the ifinerrors view"""
    title = 'Most errors on traffic in to interface'
    serieslist = 'nav.devices.*.ports.*.ifInErrors'
    graph_args = {
        'title': 'Interfaces with most errors on traffic in',
        'vtitle': 'Errors',
    }
