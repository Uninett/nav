# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2011 UNINETT AS
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

"""API that does forward and reverse DNS lookups on both IPv4 and IPv6"""

import socket
from IPy import IP
from itertools import cycle
from twisted.names import dns
from twisted.names import client
from twisted.internet import reactor
from twisted.python.failure import Failure
from twisted.names.error import DNSUnknownError
from twisted.names.error import DomainError, AuthoritativeDomainError
from twisted.names.error import DNSQueryTimeoutError, DNSFormatError 
from twisted.names.error import DNSServerError, DNSNameError
from twisted.names.error import DNSNotImplementedError, DNSQueryRefusedError 

resolvers = cycle([client.Resolver('/etc/resolv.conf') for i in range(3)])

def reverse_lookup(addresses):
    """Performs reverse lookups and returns a dict of
    ip => hostname"""
    return _lookup(addresses, _lookup_pointer, _extract_ptr)

def forward_lookup(names):
    """Performs forward lookups and returns a dict of
    hostname => list of addresses"""
    return _lookup(names, _lookup_all_records, _extract_a_and_aaaa)

def _lookup(hosts, lookup_func, callback):
    """Adds hosts to deferred, waits for results and does callback"""
    deferred_list = []

    for host in hosts:
        deferred = lookup_func(host)
        deferred.addCallback(callback, host)
        deferred.addErrback(_errback, host)
        deferred_list.append(deferred)

    while any(not deferred.called for deferred in deferred_list):
        reactor.iterate()

    return dict(deferred.result for deferred in deferred_list)
    
def _lookup_pointer(address):
    """Returns a deferred object which tries to get the hostname from ip"""
    resolver = resolvers.next()
    ip = IP(address)
    return resolver.lookupPointer(ip.reverseName())

def _lookup_all_records(name):
    """Returns a deferred object with all records related to hostname"""
    resolver = resolvers.next()
    return resolver.lookupAllRecords(name)

    
def _extract_a_and_aaaa(result, name):
    """Callback for A and AAAA records"""
    address_list = []

    for record_list in result:
        for record in record_list:
            if str(record.name) == name:
                if record.type == dns.A:
                    address_list.append(socket.inet_ntop(socket.AF_INET,
                        record.payload.address))
                elif record.type == dns.AAAA:
                    address_list.append(socket.inet_ntop(socket.AF_INET6,
                        record.payload.address))
    return (name, address_list)

def _extract_ptr(result, ip):
    """Callback for PTR records"""
    for record_list in result:
        for record in record_list:
            if record.type == dns.PTR:
                return (ip, str(record.payload.name))

def _errback(failure, host):
    """Errback"""
    return (host, failure.value)
