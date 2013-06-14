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

from __future__ import absolute_import

import logging
import re
import nav.graphite as graphite
from nav.navrrd2whisper import convert_to_whisper
from os.path import join
from nav.models.manage import Interface
from nav.models.rrd import RrdFile
from django.db.models import Q

_logger = logging.getLogger(__name__)


class Migrator(object):
    """Baseclass for migrating rrd-data to whisper files"""

    def __init__(self, basepath):
        self.basepath = basepath
        self.rrdfiles = None

    def create_path_from_metric(self, metric):
        """Create a filesystem path from a whisper metric"""
        return join(self.basepath, *metric.split('.'))

    def find_metrics(self, rrdfile):
        """Find the metrics for this rrd file"""
        raise NotImplementedError

    def migrate(self):
        """Get data from rrd-file and create one file for each datasource"""
        for rrdfile in self.rrdfiles:
            _logger.info('Migrating %s', rrdfile)
            metrics = self.find_metrics(rrdfile)
            if metrics:
                convert_to_whisper(rrdfile, metrics)


class InterfaceMigrator(Migrator):
    """Migrator for the interface rrd files"""

    def __init__(self, *args):
        super(InterfaceMigrator, self).__init__(*args)
        self.rrdfiles = RrdFile.objects.filter(key='interface')

    def find_metrics(self, rrdfile):
        try:
            interface = Interface.objects.get(pk=rrdfile.value)
        except Interface.DoesNotExist:
            _logger.error("Interface for %s does not exist", rrdfile)
            return

        hc_octets = re.compile(r'ifhc(in|out)octets', re.IGNORECASE)
        metric_mapping = {}
        for datasource in rrdfile.rrddatasource_set.all():
            descr = datasource.description
            if hc_octets.match(descr):
                descr = re.sub(r'(?i)hc', '', descr)

            metric = graphite.metric_path_for_interface(
                interface.netbox.sysname, interface.ifname, descr)
            metric_mapping[datasource.name] = \
                self.create_path_from_metric(metric)
        return metric_mapping


class SystemMigrator(Migrator):
    """Migrator for the system statistics"""

    cpus = ['cpu1min', 'cpu5min', 'hpcpu']
    memories = ['mem5minFree', 'mem5minUsed', 'hpmem5minUsed', 'hpmem5minFree']
    bandwidths = ['c1900Bandwidth', 'c1900BandwidthMax', 'c2900Bandwidth',
                  'c5000Bandwidth', 'c5000BandwidthMax']

    def __init__(self, *args):
        super(SystemMigrator, self).__init__(*args)
        self.rrdfiles = RrdFile.objects.filter(
            Q(path__endswith='routers') | Q(path__endswith='switches'))

    def find_metrics(self, rrdfile):
        """Find metrics for system datasources"""
        mapping = {}
        sysname = rrdfile.netbox.sysname
        for datasource in rrdfile.rrddatasource_set.all():
            descr = datasource.description
            if descr in self.cpus:
                metric = graphite.metric_path_for_cpu_load(
                    sysname, 'cpu', self.get_interval(descr))
            elif descr in self.memories:
                metric = graphite.metric_prefix_for_memory(sysname, descr)
            elif descr in self.bandwidths:
                if descr.endswith(('Max', 'max')):
                    if descr.startswith('c5000'):
                        metric = graphite.metric_path_for_bandwith_peak(
                            sysname, True)
                    else:
                        metric = graphite.metric_path_for_bandwith_peak(
                            sysname, False)
                else:
                    if descr.startswith('c5000'):
                        metric = graphite.metric_path_for_bandwith(
                            sysname, True)
                    else:
                        metric = graphite.metric_path_for_bandwith(
                            sysname, False)
            elif descr == 'sysUpTime':
                metric = graphite.metric_path_for_sysuptime(sysname)
            else:
                _logger.info('Could not find metric for %s' % descr)
                continue

            mapping[datasource.name] = self.create_path_from_metric(metric)

        return mapping

    def get_interval(self, descr):
        """Finds the interval in a datasource description"""
        matchobject = re.search(r'\d+', descr)
        if matchobject:
            return matchobject.group()


class PpingMigrator(Migrator):
    """Migrator for pping statistics"""

    def __init__(self, *args):
        super(PpingMigrator, self).__init__(*args)
        self.rrdfiles = RrdFile.objects.filter(subsystem='pping')

    def find_metrics(self, rrdfile):
        """Find metric mapping for pping datasources"""
        mapping = {}
        sysname = rrdfile.netbox.sysname
        for datasource in rrdfile.rrddatasource_set.all():
            if datasource.name == 'RESPONSETIME':
                metric = graphite.metric_path_for_roundtrip_time(sysname)
            elif datasource.name == 'STATUS':
                metric = graphite.metric_path_for_packet_loss(sysname)
            else:
                _logger.error('Could not find metric for %s', datasource.name)
                continue
            mapping[datasource.name] = self.create_path_from_metric(metric)

        return mapping


class SensorMigrator(Migrator):
    """Migrator for sensor statistics"""

    def __init__(self, *args):
        super(SensorMigrator, self).__init__(*args)
        self.rrdfiles = RrdFile.objects.filter(key='sensor')

    def find_metrics(self, rrdfile):
        return super(SensorMigrator, self).find_metrics(rrdfile)
