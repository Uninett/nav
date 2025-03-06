#
# Copyright (C) 2008-2011 Uninett AS
# Copyright (C) 2022 Sikt
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
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Asynchronous DNS resolver for lookups on both IPv4 and IPv6.

The API is designed for use in synchronous programs and uses Twisted in
perverted ways to accomplish the behind-the-curtain asynchronous work.

We would rather have used adns, but the available versions have poor IPv6
support.

"""

import socket
from itertools import cycle
from collections import defaultdict

from IPy import IP
from twisted.names import dns
from twisted.names import client
from twisted.internet import defer, task

from twisted.internet import reactor

from twisted.names.error import DNSUnknownError
from twisted.names.error import DomainError, AuthoritativeDomainError
from twisted.names.error import DNSQueryTimeoutError, DNSFormatError
from twisted.names.error import DNSServerError, DNSNameError
from twisted.names.error import DNSNotImplementedError, DNSQueryRefusedError

__all__ = [
    "reverse_lookup",
    "forward_lookup",
    "Resolver",
    "ForwardResolver",
    "ReverseResolver",
    "DNSUnknownError",
    "DomainError",
    "AuthoritativeDomainError",
    "DNSQueryTimeoutError",
    "DNSFormatError",
    "DNSServerError",
    "DNSNameError",
    "DNSNotImplementedError",
    "DNSQueryRefusedError",
]


BATCH_SIZE = 100


def reverse_lookup(addresses):
    """Runs parallel reverse DNS lookups for addresses.

    :returns: A dict of {address: [name, ...]} items

    """
    resolver = ReverseResolver()
    return resolver.resolve(addresses)


def forward_lookup(names):
    """Runs parallel forward DNS lookups for names.

    :returns: A dict of {name: [address, ...]} items

    """
    resolver = ForwardResolver()
    return resolver.resolve(names)


class Resolver(object):
    """Abstract base class for resolvers"""

    def __init__(self):
        self._resolvers = cycle(
            [client.Resolver("/etc/resolv.conf") for _i in range(3)]
        )
        self.results = defaultdict(list)
        self._finished = False
        self._errors = []

    def resolve(self, names):
        """Resolves DNS names in parallel"""
        self.results = defaultdict(list)
        self._finished = False
        self._errors = []

        def lookup_names():
            for name in names:
                for deferred in self.lookup(name):
                    deferred.addCallback(self._extract_records, name)
                    deferred.addErrback(self._errback, name)
                    deferred.addCallback(self._save_result)
                    yield deferred

        # Limits the number of parallel requests to BATCH_SIZE
        coop = task.Cooperator()
        work = lookup_names()
        deferred_list = defer.DeferredList(
            [
                coop.coiterate(work).addErrback(self._save_error)
                for _ in range(BATCH_SIZE)
            ]
        )
        deferred_list.addCallback(self._finish)

        while not self._finished:
            reactor.iterate()
        # Although the results are in at this point, we may need an extra
        # iteration to ensure the resolver library closes its UDP sockets
        reactor.iterate()

        # raise first error if any occurred
        for error in self._errors:
            raise error

        return dict(self.results)

    def lookup(self, name):
        """Initiates possibly multiple asynchronous DNS lookups for a name"""
        raise NotImplementedError

    @staticmethod
    def _extract_records(result, name):
        raise NotImplementedError

    def _save_result(self, result):
        name, response = result
        if isinstance(response, Exception):
            self.results[name] = response
        else:
            self.results[name].extend(response)

    @staticmethod
    def _errback(failure, host):
        """Errback"""
        return host, failure.value

    def _save_error(self, failure):
        """Errback for coiterator. Saves error so it can be raised later"""
        self._errors.append(failure.value)

    def _finish(self, _):
        self._finished = True


class ForwardResolver(Resolver):
    """A forward resolver implementation for A and AAAA record lookups.

    NOTE: It will not lookup and follow CNAME records.

    """

    def lookup(self, name):
        """Returns a deferred object with all records related to hostname"""

        if isinstance(name, str):
            name = name.encode("idna")

        resolver = next(self._resolvers)
        return [resolver.lookupAddress(name), resolver.lookupIPV6Address(name)]

    @staticmethod
    def _extract_records(result, name):
        """Callback for A and AAAA records"""
        address_list = []

        for record_list in result:
            for record in record_list:
                if str(record.name).lower() == name.lower():
                    if record.type == dns.A:
                        address_list.append(
                            socket.inet_ntop(socket.AF_INET, record.payload.address)
                        )
                    elif record.type == dns.AAAA:
                        address_list.append(
                            socket.inet_ntop(socket.AF_INET6, record.payload.address)
                        )
        return name, address_list


class ReverseResolver(Resolver):
    """Reverse resolver implementation for PTR record lookups"""

    def lookup(self, address):
        """Returns a deferred object which tries to get the hostname from ip"""
        resolver = next(self._resolvers)
        ip = IP(address)
        return [resolver.lookupPointer(ip.reverseName())]

    @staticmethod
    def _extract_records(result, ip):
        """Callback for PTR records"""
        name_list = []

        for record_list in result:
            for record in record_list:
                if record.type == dns.PTR:
                    name_list.append(str(record.payload.name))

        return ip, name_list
