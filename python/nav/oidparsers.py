#
# Copyright (C) 2016 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Various functions that can be used to parse the contents of compound SNMP table
row indexes.

Most of the functions here do not follow the correct naming pattern,
as defined by PEP-8, because their names are derived directly from SNMP MIB
objects.

"""

import array
from functools import partial
from itertools import islice
from struct import unpack

from IPy import IP

from .oids import OID

IPV4_ID = 1
IPV6_ID = 2


def consume(sequence, *consumers):
    """
    Consumes an OID sequence, using a list of provided consumer functions,
    yielding the consumer results as they are returned.

    :param sequence: An iterable OID sequence
    :param consumers: A list of functions that each will consume parts of the
                      sequence.
    :return: A generator yielding one element for each of the supplied consumer
             functions - unless the sequence isn't long enough to feed to all
             the consumers, in which case things will probably error out.

    """
    iterator = iter(sequence)
    for consumer in consumers:
        yield consumer(iterator)


####################
# Helper functions #
####################


def oid_to_ipv6(oid):
    """Converts a sequence of 16 numbers to an IPv6 object in the fastest
    known way.

    :param oid: Any list or tuple of 16 integers

    """
    if len(oid) != 16:
        raise ValueError("IPv6 address must be 16 octets, not %d" % len(oid))
    try:
        high, low = unpack("!QQ", array.array("B", oid).tobytes())
    except OverflowError as error:
        raise ValueError(error)
    addr = (high << 64) + low
    return IP(addr, ipversion=6)


def oid_to_ipv4(oid):
    """Converts a sequence of 4 numbers to an IPv4 object in the fastest
    known way.

    :param oid: Any list or tuple of 4 integers.

    """
    if len(oid) != 4:
        raise ValueError("IPv4 address must be 4 octets, not %d" % len(oid))
    try:
        (addr,) = unpack("!I", array.array("B", oid).tobytes())
    except OverflowError as error:
        raise ValueError(error)
    return IP(addr, ipversion=4)


#############################################################################
# Varios OID consumer functions, which can be fed to the consume() function #
#############################################################################


def Unsigned32(iterator):
    """Consume a single element"""
    return next(iterator)


def String(iterator, length=None):
    """Consume a string of a length specified by the next iteration"""
    if length is None:
        length = next(iterator)
    return OID(islice(iterator, length))


ObjectIdentifier = String
InetAddressType = Unsigned32
InetAddress = String
InetAddressIPv4 = partial(String, length=4)
InetAddressIPv6 = partial(String, length=16)
InetAddressPrefixLength = Unsigned32


def TypedInetAddress(iterator):
    """
    Consumes and parses a InetAddressType.InetAddress combo into an IPy.IP host
    address.
    """
    addr_type, addr = consume(iterator, InetAddressType, InetAddress)
    if addr_type == IPV4_ID:
        return oid_to_ipv4(addr)
    elif addr_type == IPV6_ID:
        return oid_to_ipv6(addr)


def TypedFixedInetAddress(iterator):
    """
    Consumes and parses a InetAddressType.InetAddress combo, where there is
    no length specifier in the InetAddress string, into an IPy.IP host address.
    """
    addr_type = next(iterator)
    if addr_type == IPV4_ID:
        (addr,) = consume(iterator, InetAddressIPv4)
        return oid_to_ipv4(addr)
    elif addr_type == IPV6_ID:
        (addr,) = consume(iterator, InetAddressIPv6)
        return oid_to_ipv6(addr)
    else:
        raise ValueError("unsupported address type %s", addr_type)


def InetPrefix(iterator):
    """
    Consumes and parses a InetAddressType.InetAddress.InetAddressPrefixLength
    combo into an IPy.IP network prefix address
    """
    addr, mask = consume(iterator, TypedInetAddress, InetAddressPrefixLength)
    if addr:
        return addr.make_net(mask)
