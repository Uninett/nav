#!/usr/bin/env python
#
# Copyright (C) 2014 UNINETT AS
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
"""
This module implements migrator classes for migrating rrd data to whisper data
"""

from __future__ import absolute_import

import logging
import re
from nav.metrics.templates import (
    metric_path_for_bandwith,
    metric_path_for_interface,
    metric_path_for_cpu_load,
    metric_prefix_for_memory,
    metric_path_for_bandwith_peak,
    metric_path_for_sysuptime,
    metric_path_for_roundtrip_time,
    metric_path_for_packet_loss,
    metric_path_for_sensor,
    metric_path_for_prefix,
    metric_path_for_service_availability,
    metric_path_for_service_response_time)
from nav.navrrd2whisper import convert_to_whisper
from os.path import join
from nav.models.manage import Interface, Sensor, Prefix, Netbox
from nav.models.service import Service
from nav.models.rrd import RrdFile
from django.db.models import Q

_logger = logging.getLogger(__name__)


class Migrator(object):
    """Baseclass for migrating rrd-data to whisper files"""

    def __init__(self, basepath):
        self.basepath = basepath  # Base path for storing the whisper files
        self.rrdfiles = None
        self.infoclass = None  # See key/value in rrd_file
        self.extra_retention = None  # Tuple with extra retention(seconds only)

    def create_path_from_metric(self, metric):
        """Create a filesystem path from a whisper metric"""
        return join(self.basepath, *metric.split('.'))

    def migrate(self):
        """Get data from rrd-file and create one file for each datasource"""
        for rrdfile in self.rrdfiles:
            _logger.info('Migrating %s', rrdfile)
            mapping = self.find_metrics(rrdfile)
            if mapping:
                try:
                    convert_to_whisper(rrdfile, mapping, self.extra_retention)
                except Exception:
                    _logger.exception("Unhandled error during conversion of %r",
                                      rrdfile)

    def find_metrics(self, rrdfile):
        """Find metrics for datasources"""
        mapping = {}
        try:
            sysname = rrdfile.netbox.sysname
        except Netbox.DoesNotExist:
            sysname = None

        info_object = None

        if self.infoclass:
            try:
                info_object = self.infoclass.objects.get(pk=rrdfile.value)
            except self.infoclass.DoesNotExist, error:
                _logger.error(error)
                return

        for datasource in rrdfile.rrddatasource_set.all():
            metric = self.find_metric(datasource, sysname, info_object)
            if metric:
                mapping[datasource.name] = {
                    'path': self.create_path_from_metric(metric),
                    'metric': metric}

        return mapping

    def find_metric(self, datasource, sysname=None, info_object=None):
        """Returns the metric for this datasource

        :param datasource: Datasource with metainfo
        :param sysname: Sysname for the netbox
        :param info_object: Optional object with additional metainfo

        """
        raise NotImplementedError


class InterfaceMigrator(Migrator):
    """Migrator for the interface rrd files"""

    def __init__(self, *args):
        super(InterfaceMigrator, self).__init__(*args)
        self.rrdfiles = RrdFile.objects.filter(key='interface')
        self.infoclass = Interface

    def find_metric(self, datasource, sysname=None, info_object=None):
        hc_octets = re.compile(r'ifhc(in|out)octets', re.IGNORECASE)
        descr = datasource.description
        if hc_octets.match(descr):
            descr = re.sub(r'(?i)hc', '', descr)
        return metric_path_for_interface(
            info_object.netbox.sysname, info_object.ifname, descr)


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
        self.extra_retention = (60, 60 * 60 * 24)

    def find_metric(self, datasource, sysname=None, info_object=None):
        descr = datasource.description
        if descr in self.cpus:
            metric = metric_path_for_cpu_load(
                sysname, 'cpu', self.get_interval(descr))
        elif descr in self.memories:
            metric = metric_prefix_for_memory(sysname, descr)
        elif descr in self.bandwidths:
            if descr.endswith(('Max', 'max')):
                if descr.startswith('c5000'):
                    metric = metric_path_for_bandwith_peak(
                        sysname, True)
                else:
                    metric = metric_path_for_bandwith_peak(
                        sysname, False)
            else:
                if descr.startswith('c5000'):
                    metric = metric_path_for_bandwith(
                        sysname, True)
                else:
                    metric = metric_path_for_bandwith(
                        sysname, False)
        elif descr == 'sysUpTime':
            metric = metric_path_for_sysuptime(sysname)
        else:
            _logger.info('Could not find metric for %s' % descr)
            metric = None

        return metric

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
        self.extra_retention = (20, 60 * 60 * 12)

    def find_metric(self, datasource, sysname=None, info_object=None):
        if datasource.name == 'RESPONSETIME':
            return metric_path_for_roundtrip_time(sysname)
        elif datasource.name == 'STATUS':
            return metric_path_for_packet_loss(sysname)
        else:
            _logger.error('Could not find metric for %s', datasource.name)


class ServicePingMigrator(Migrator):
    """Migrator for serviceping statistics"""

    def __init__(self, *args):
        super(ServicePingMigrator, self).__init__(*args)
        self.rrdfiles = RrdFile.objects.filter(subsystem='serviceping')
        self.infoclass = Service

    def find_metric(self, datasource, sysname=None, info_object=None):
        if datasource.name == 'STATUS':
            return metric_path_for_service_availability(sysname,
                                                        info_object.handler,
                                                        info_object.id)
        elif datasource.name == 'RESPONSETIME':
            return metric_path_for_service_response_time(sysname,
                                                         info_object.handler,
                                                         info_object.id)
        else:
            _logger.error('Could not find metric for %s', datasource.name)


class SensorMigrator(Migrator):
    """Migrator for sensor statistics"""

    def __init__(self, *args):
        super(SensorMigrator, self).__init__(*args)
        self.rrdfiles = RrdFile.objects.filter(key='sensor')
        self.infoclass = Sensor

    def find_metric(self, datasource, sysname=None, info_object=None):
        return metric_path_for_sensor(sysname, info_object.name)


class ActiveIpMigrator(Migrator):
    """Migrator for active ip statistics"""

    def __init__(self, *args):
        super(ActiveIpMigrator, self).__init__(*args)
        self.rrdfiles = RrdFile.objects.filter(category='activeip')
        self.infoclass = Prefix

    def find_metric(self, datasource, sysname=None, info_object=None):
        return metric_path_for_prefix(info_object, datasource.name)
