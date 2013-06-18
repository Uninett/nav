#!/usr/bin/env python
#
# Copyright (C) 2012 UNINETT AS
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
"""Controller for all rrd-activity regarding creating and updating rrd-files"""

import logging
import rrdtool

LOG = logging.getLogger('ipcollector.rrdcontroller')


def create_rrdfile(element, when):
    """Create rrdfile"""
    LOG.debug('Creating rrdfile %s', element.fullpath)

    rras = ['RRA:AVERAGE:0.5:1:600',
            'RRA:AVERAGE:0.5:6:600',
            'RRA:AVERAGE:0.5:24:600',
            'RRA:MAX:0.5:24:600',
            'RRA:AVERAGE:0.5:96:600',
            'RRA:MAX:0.5:96:600']
    datasources = ['DS:ip_count:GAUGE:3600:0:100000',
                   'DS:mac_count:GAUGE:3600:0:100000',
                   'DS:ip_range:GAUGE:3600:0:100000']

    arguments = [element.fullpath]
    arguments.extend(['--step', '1800'])
    arguments.extend(['--start', str(when - 1800)])
    arguments.extend(datasources)
    arguments.extend(rras)
    rrdtool.create(arguments)


def update_rrdfile(element, when):
    """Update this rrdfile with given data"""
    values = [when,
              element.ip_count,
              element.mac_count,
              element.ip_range]
    values_as_string = ":".join([str(x) for x in values])
    LOG.debug('Updating %s -> %s' % (element.fullpath, values_as_string))
    rrdtool.update([element.fullpath, values_as_string])


def update_rrddb():
    """Update rrd database with metainfo"""
    pass
