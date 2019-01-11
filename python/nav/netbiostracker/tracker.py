#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details. You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Module for doing netbios scans"""
import logging
from collections import namedtuple
from datetime import datetime
from functools import wraps
from time import time
from subprocess import Popen, PIPE
from nav.models.manage import Arp, Netbios
from nav.macaddress import MacAddress
from django.db import transaction
from django.utils import six

SPLITCHAR = '!'

# pylint: disable=C0103
NetbiosResult = namedtuple('NetbiosResult',
                           'ip name server username mac')

_logger = logging.getLogger(__name__)


def timed(f):
    """Decorator to time execution of functions"""
    @wraps(f)
    def wrapper(*args, **kwds):
        """Decorator"""
        start = time()
        result = f(*args, **kwds)
        elapsed = time() - start
        _logger.debug("%s took %f seconds to finish", f.__name__, elapsed)
        return result
    return wrapper


@timed
def get_addresses_to_scan(exclude_list=None):
    """Get ip-addresses to scan

    This function should return a list of the active ip-addresses in the
    database excluding the ip-addresses from the exclude list.

    """
    _logger.debug('Getting addresses to scan')
    if not exclude_list:
        exclude_list = []

    def _is_excluded(ip):
        for excluded_addr in exclude_list:
            if ip in excluded_addr:
                return True
        return False

    addresses = Arp.objects.filter(end_time__gte=datetime.max).extra(
        where=['family(ip)=4']).distinct('ip').values_list('ip', flat=True)
    return [str(ip) for ip in addresses if not _is_excluded(ip)]


@timed
def scan(addresses):
    """Scan a list of ip-addresses for netbios names"""

    _logger.debug('Scanning %s addresses', len(addresses))
    proc = Popen(['nbtscan', '-f-', '-s', SPLITCHAR], stdin=PIPE, stdout=PIPE)
    stdout, stderr = proc.communicate('\n'.join(addresses))
    if stderr:
        raise Exception(stderr)

    if isinstance(stdout, six.binary_type):
        stdout = stdout.decode('cp850')  # cp850 seems like netbios' standard

    _logger.debug('Result from scan:\n%s', stdout)
    return stdout


@timed
def parse(output, encoding=None):
    """Parse the results from a netbios scan"""

    results = output.split('\n')
    parsed_results = []
    for result in results:
        if result:
            try:
                args = [x.strip() for x in result.split(SPLITCHAR)]
                netbiosresult = NetbiosResult(*args)
                # Handle mac address with "-" separator (FreeBSD nbtscan).
                netbiosresult = netbiosresult._replace(
                    mac=str(MacAddress(netbiosresult.mac)))
            except (TypeError, ValueError):
                _logger.error('Error parsing %s', result)
            else:
                parsed_results.append(netbiosresult)

    return parsed_results


@timed
def update_database(netbiosresults):
    """Update database with results from a scan

    3 scenarios:

    1: If a similar entry with end_time = infinity exists in the database
       and in the result set, do nothing.
    2: If a similar entry with end_time = infinity exists in the database
       but not in the result set, set end_time = now
    3: If a similar entry does not exist, create a new entry

    """

    scan_set = set(netbiosresults)
    database_entries = fetch_database_entries()
    database_set = set(database_entries)

    entries_to_end = database_set - scan_set
    entries_to_create = scan_set - database_set

    set_end_time(database_entries, entries_to_end)
    create_entries(entries_to_create)


@timed
def fetch_database_entries():
    """Fetch current active entries from netbios table

    Create a structure that is suitable for comparing as a set with other
    structures

    """
    database_entries = {}
    for entry in Netbios.objects.filter(end_time=datetime.max):
        database_entries[(entry.ip, entry.name, entry.server, entry.username,
                          entry.mac)] = entry
    return database_entries


@timed
@transaction.atomic()
def set_end_time(database_entries, entries_to_end):
    """End the entries given"""
    _logger.debug('Ending %s entries', len(entries_to_end))
    for key in entries_to_end:
        entry = database_entries[key]
        entry.end_time = datetime.now()
        entry.save()


@timed
@transaction.atomic()
def create_entries(entries_to_create):
    """Create new netbios entries for the data given"""
    _logger.debug('Creating %s new entries', len(entries_to_create))
    for entry in entries_to_create:
        netbios = Netbios(ip=entry.ip, mac=entry.mac or None, name=entry.name,
                          server=entry.server, username=entry.username)
        netbios.save()
