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

# pylint: disable=C0103

import logging
import rrdtool
import time

from collections import namedtuple
from IPy import IP
from os import listdir, unlink
from os.path import exists, join

from nav.models.manage import Prefix
from nav.models.rrd import RrdFile, RrdDataSource

from django.db import DatabaseError
from django.db.transaction import commit_on_success, set_dirty

import nav.activeipcollector.collector as collector
import nav.activeipcollector.rrdcontroller as rrdcontroller

Element = namedtuple('Element',
                     'prefix ip_type ip_count mac_count ip_range filename '
                     'fullpath')

LOG = logging.getLogger('ipcollector.manager')
DATABASE_CATEGORY = 'activeip'


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
    """Store data in rrd-files and update rrd-database

    data: a cursor.fetchall object containing all database rows we are to store
    where: the path to the rrd-files
    """
    errors = 0
    successful = 0  # Number of successful rrd-file updates
    has_stored = []
    for db_tuple in data:
        try:
            element = store_tuple(db_tuple, where)
            successful += 1

            # If we store data for several days, has_stored keeps track of
            # this so that we don't update the rrd-database several times
            # with the same info.
            if element.prefix not in has_stored:
                update_rrddb(element, where)
                has_stored.append(element.prefix)
        except rrdtool.error, error:
            LOG.error(error)
            errors += 1

    LOG.info('%s updates (%s errors) for %s prefixes' % (successful, errors,
                                                         len(data)))

    return errors


def store_tuple(db_tuple, where):
    """Store data from the db_tuple in an rrd file

    db_tuple: a row from a rrd_fetchall object
    where: path to rrd_files
    """
    prefix, timestamp, ip_count, mac_count = db_tuple
    when = get_timestamp(timestamp)
    filename = convert_to_filename(prefix)
    element = Element(prefix, find_type(prefix), ip_count, mac_count,
                      find_range(prefix), filename, join(where, filename))

    if not exists(element.fullpath):
        rrdcontroller.create_rrdfile(element, when)

    rrdcontroller.update_rrdfile(element, when)
    return element


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
        try:
            rrdfile = RrdFile.objects.get(category=DATABASE_CATEGORY,
                                          key='prefix', value=prefix.id)
        except RrdFile.DoesNotExist:
            create_rrddb_file(element, prefix, datapath)
        else:
            rrdfile.path = datapath
            rrdfile.filename = element.filename
            rrdfile.save()
    except DatabaseError, error:
        LOG.error(error)


@commit_on_success
def create_rrddb_file(element, prefix, datapath):
    """Create an rrd_file"""
    LOG.debug('Creating rrd_file for %s' % element.prefix)

    Datasource = namedtuple("Datasource", "name descr unit")

    rrdfile = RrdFile(
        path=datapath,
        filename=element.filename,
        step=1800,
        key='prefix',
        value=prefix.id,
        category=DATABASE_CATEGORY
    )

    set_dirty()  # Why do I need to do this?
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
        rrd_file=rrdfile,
        name=datasource.name,
        description=datasource.descr,
        type=RrdDataSource.TYPE_GAUGE,
        units=datasource.unit,
        threshold_state=None,
        delimiter=None
    )
    rrdds.save()
