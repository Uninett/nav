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

    def find_metrics(self, rrdfile):
        """Find metrics for the datasources in the rrdfile"""
        raise NotImplementedError

    def create_path_from_metric(self, metric):
        """Create a filesystem path from a whisper metric"""
        return join(self.basepath, *metric.split('.'))

    def migrate(self):
        """Get data from rrd-file and create one file for each datasource"""
        raise NotImplementedError


class InterfaceMigrator(Migrator):
    """Migrator for the interface rrd files"""

    def find_metrics(self, rrdfile, interface):
        """Find the metrics for this rrd file"""
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

    def migrate(self):
        rrdfiles = RrdFile.objects.filter(
            key='interface').order_by('netbox', 'filename')
        for rrdfile in rrdfiles:
            _logger.info('Migrating %s', rrdfile)
            try:
                interface = Interface.objects.get(pk=rrdfile.value)
            except Interface.DoesNotExist:
                _logger.error("Interface for %s does not exist", rrdfile)
            else:
                metrics = self.find_metrics(rrdfile, interface)
                convert_to_whisper(rrdfile, metrics)


class SystemMigrator(Migrator):
    """Migrator for the system statistics"""

    cpus = ['cpu1min', 'cpu5min', 'hpcpu']
    memories = ['mem5minFree', 'mem5minUsed', 'hpmem5minUsed', 'hpmem5minFree']
    bandwidths = ['c1900Bandwidth', 'c1900BandwidthMax', 'c2900Bandwidth',
                  'c5000Bandwidth', 'c5000BandwidthMax']

    def find_metrics(self, rrdfile):
        """Find metrics for system datasources"""
        mapping = {}
        sysname = rrdfile.netbox.sysname
        for datasource in rrdfile.rrddatasource_set.all():
            descr = datasource.description
            if descr in self.cpus:
                metric = graphite.metric_path_for_cpu_load(
                    sysname, 'cpu',self.get_interval(descr))
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

    def migrate(self):
        rrdfiles = RrdFile.objects.filter(Q(path__endswith='routers') |
                                          Q(path__endswith='switches'))
        for rrdfile in rrdfiles:
            convert_to_whisper(rrdfile, self.find_metrics(rrdfile))


class PpingMigrator(Migrator):

    def find_metrics(self, rrdfile):
        mapping = {}
        sysname = rrdfile.netbox.sysname
        for datasource in rrdfile.rrddatasource_set.all():
            mapping[datasource.name] = graphite.metric_prefix_for_system(sysname)


    def migrate(self):
        rrdfiles = RrdFile.objects.filter(subsystem='pping')
        for rrdfile in rrdfiles:
            convert_to_whisper(rrdfile, self.find_metrics(rrdfile))

