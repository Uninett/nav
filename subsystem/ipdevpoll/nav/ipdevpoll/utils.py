# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
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
"""Utility functions for ipdevpoll."""

import logging
import gc
from functools import wraps

from IPy import IP

import django.db
from django.db import transaction
from django.conf import settings

from twisted.internet.defer import Deferred
from twisted.internet import reactor

_logger = logging.getLogger(__name__)

def fire_eventually(result):
    """This returns a Deferred which will fire in a later reactor turn.

    Can be used to cause a break in deferred chain, so the number of
    stack frames won't exceed sys.getrecursionlimit().  Do like this:

    >>> deferred_chain.addCallback(lambda thing: fire_eventually(thing))

    Reference:
    http://twistedmatrix.com/pipermail/twisted-python/2008-November/018693.html

    """
    deferred = Deferred()
    reactor.callLater(0, deferred.callback, result)
    return deferred

def binary_mac_to_hex(binary_mac):
    """Converts a binary string MAC address to hex string.

    Only the first 6 octets will be converted, any more will be
    ignored. If the address contains less than 6 octets, the result will be
    padded with leading zeros.

    """
    if binary_mac:
        if len(binary_mac) < 6:
            binary_mac = "\x00" * (6 - len(binary_mac)) + binary_mac
        return ":".join("%02x" % ord(x) for x in binary_mac[:6])

def truncate_mac(mac):
    """Takes a MAC address on the form xx:xx:xx... of any length and returns
    the first 6 parts.
    """
    parts = mac.split(':')
    if len(parts) > 6:
        mac = ':'.join(parts[:6])
    return mac

def find_prefix(ip, prefix_list):
    """Takes an IPy.IP object and a list of manage.Prefix and returns the most
    precise prefix the IP matches.
    """
    ret = None
    for p in prefix_list:
        sub = IP(p.net_address)
        if ip in sub:
            # Return the most precise prefix, ie the longest prefix
            if not ret or IP(ret.net_address).prefixlen() < sub.prefixlen():
                ret = p
    return ret

def is_invalid_utf8(string):
    """Returns True if string is invalid UTF-8.

    If string is not a an str object, or is decodeable as UTF-8, False is
    returned.

    """
    if isinstance(string, str):
        try:
            string.decode('utf-8')
        except UnicodeDecodeError, e:
            return True
    return False

def django_debug_cleanup():
    """Resets Django's list of logged queries.

    When DJANGO_DEBUG is set to true, Django will log all generated SQL queries
    in a list, which grows indefinitely.  This is ok for short-lived processes;
    not so much for daemons.  We may want those queries in the short-term, but
    in the long-term the ever-growing list is uninteresting and also bad.

    This should be called once-in-a-while from every thread that has Django
    database access, as the queries list is stored in thread-local data.

    """
    query_count = len(django.db.connection.queries)
    if query_count:
        _logger.debug("Removing %d logged Django queries", query_count)
        django.db.reset_queries()
        gc.collect()

def commit_on_success(func):
    """Decorates func such that the current Django transaction is committed on
    successful return.

    If func raises an exception, the current transaction is rolled back.

    Why don't we use django.db.transaction.commit_on_success()? Because it does
    not commit or rollback unless Django actually tried to change something in
    the database. It was designed with short-lived web request cycles in mind.
    This gives us two problems:

    1. If the transaction consisted of read-only operations, the connection
       will stay idle inside a transaction, and that's bad.

    2. If a database error occurred inside a transaction, the connection would
       be useless until the transaction is rolled back.  Any further attempts
       to use the same connection will result in more errors, and a long-lived
       process will keep spewing error messages.

    """
    def _commit_on_success(*args, **kwargs):
        try:
            transaction.enter_transaction_management()
            transaction.managed(True)
            try:
                result = func(*args, **kwargs)
            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()
            return result
        finally:
            transaction.leave_transaction_management()
    return wraps(func)(_commit_on_success)

def cleanup_django_debug_after(func):
    """Decorates func such that django_debug_cleanup is run after func.

    Even if func raises an exception, the cleanup will be run.

    """
    def _cleanup(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            django_debug_cleanup()
    return wraps(func)(_cleanup)

