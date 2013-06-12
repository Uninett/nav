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

import re
import nav.graphite as graphite
from nav.navrrd2whisper import convert_to_whisper
from os.path import join
from nav.models.manage import Interface
from nav.models.rrd import RrdFile


class Migrator(object):
    """Baseclass for migrating rrd-data to whisper files"""

    def __init__(self, basepath):
        self.basepath = basepath

    def create_path_from_metric(self, metric):
        """Create a filesystem path from a whisper metric"""
        return join(self.basepath, *metric.split('.'))

    @classmethod
    def migrate(cls):
        """Get data from rrd-file and create one file for each datasource"""
        return NotImplemented


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
            metric_mapping[datasource.name] = join(
                self.basepath, self.create_path_from_metric(metric))
        return metric_mapping

    def migrate(self):
        rrdfiles = RrdFile.objects.filter(
            key='interface').order_by('netbox', 'filename')
        for rrdfile in rrdfiles:
            try:
                interface = Interface.objects.get(pk=rrdfile.value)
            except Interface.DoesNotExist:
                print "Interface for %s does not exist" % rrdfile
            else:
                metrics = self.find_metrics(rrdfile, interface)
                convert_to_whisper(str(join(rrdfile.path, rrdfile.filename)),
                                   metrics)
