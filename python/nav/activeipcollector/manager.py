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
"""Manage collection and storing of active ip-addresses statistics"""

import logging
import rrdtool
import time

from collections import namedtuple
from IPy import IP
from os import listdir, unlink
from os.path import exists, join

from nav.models.manage import Prefix
from nav.models.rrd import RrdFile, RrdDataSource
import nav.activeipcollector.collector as collector
import nav.activeipcollector.rrdcontroller as rrdcontroller

Element = namedtuple('Element',
                     'prefix ip_type ip_count mac_count ip_range filename')

LOG = logging.getLogger('ipcollector.manager')

def run(datadir, days=None, reset=False):
    """Fetch active ip"""

    if reset:
        delete_files(datadir)

    return store(collector.collect(days), datadir)


def delete_files(datadir):
    """Deletes all files in this directory"""
    for rrdfile in listdir(datadir):
        filepath = join(datadir, rrdfile)
        try:
            LOG.info('Deleting %s' % filepath)
            unlink(filepath)
        except OSError, error:
            LOG.error("Error deleting file %s: %s" % (filepath, error))


def store(data, where):
    """Store data"""
    errors = 0
    for db_tuple in data:
        try:
            store_tuple(db_tuple, where)
        except rrdtool.error, error:
            LOG.error(error)
            errors += 1

    return errors


def store_tuple(db_tuple, where):
    """Store this database tuple"""
    prefix, timestamp, ip_count, mac_count = db_tuple
    when = get_timestamp(timestamp)
    element = Element(prefix, find_type(prefix), ip_count, mac_count,
                      find_range(prefix),
                      create_fully_qualified_filename(prefix, where))

    if not exists(element.filename):
        rrdcontroller.create_rrdfile(element.filename, when)

    rrdcontroller.update_rrdfile(element, when)
    update_rrddb(element, where)


def find_type(prefix):
    """Find ip type (4 or 6) of prefix"""
    try:
        return IP(prefix).iptype()
    except ValueError:
        return None


def find_range(prefix):
    """
    Find the max number of ip-addresses that are available for hosts
    on this prefix
    """
    try:
        ip = IP(prefix)
        if ip.version() == 4 and ip.len() > 2:
            return ip.len() - 2
        return 0
    except ValueError:
        return 0


def create_fully_qualified_filename(prefix, where):
    """Create full path to this rrd-file"""
    return join(where, convert_to_filename(prefix))


def convert_to_filename(prefix):
    """Convert this prefix to a suitable filename"""
    blacklist = ['/', '.', ':']
    replacement = '_'
    for item in blacklist:
        prefix = prefix.replace(item, replacement)

    return prefix + '.rrd'


def get_timestamp(timestamp=None):
    """Find timestamp closest to 30 minutes intervals"""

    def get_epoch():
        """Find epoch from a datetime object"""
        return int(time.mktime(timestamp.timetuple()))

    halfhour = 60 * 30
    epoch = get_epoch() if timestamp else int(time.time())
    difference = epoch % halfhour
    if difference > halfhour / 2:
        epoch += (halfhour - difference)
    else:
        epoch -= difference

    return epoch


def update_rrddb(element, datapath):
    """Create a row for this element in the RRD-database"""
    try:
        prefix = Prefix.objects.get(net_address=element.prefix)
    except Prefix.DoesNotExist:
        LOG.error('Could not find prefix %s in database' % element.prefix)
        return

    try:
        rrdfile = RrdFile.objects.get(key='prefix', value=prefix.id)

        LOG.debug('This rrdfile already exists: %s' % element.prefix)

        rrdfile.path = datapath
        rrdfile.filename = element.filename
        rrdfile.save()
    except RrdFile.DoesNotExist:
        create_rrddb_file(element, prefix, datapath)


def create_rrddb_file(element, prefix, datapath):
    """Create an rrd_file"""
    LOG.debug('Creating rrd_file for %s' % element.prefix)

    Datasource = namedtuple("Datasource", "name descr unit")

    rrdfile = RrdFile(
        path = datapath,
        filename = element.filename,
        step = 1800,
        key = 'prefix',
        value = prefix.id,
        category = 'activeip'
    )
    rrdfile.save()

    datasources = [
        Datasource('ip_count', 'Number of ip-addresses on this prefix',
                   'ip-addresses'),
        Datasource('mac_count', 'Number of mac-addresses on this prefix',
                   'mac-addresses'),
        Datasource('ip_range',
                   'Total number of ip-addresses available on this prefix',
                   'ip-addresses'),
    ]

    for datasource in datasources:
        create_rrddb_datasource(rrdfile, datasource)


def create_rrddb_datasource(rrdfile, datasource):
    """Create an rrd_datasource"""
    LOG.debug('Creating rrd_datasource for %s' % datasource.name)

    rrdds = RrdDataSource(
        rrd_file = rrdfile,
        name = datasource.name,
        description = datasource.descr,
        type = RrdDataSource.TYPE_GAUGE,
        units = datasource.unit,
        threshold_state = None,
        delimiter = None
    )
    rrdds.save()
