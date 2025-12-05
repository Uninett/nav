# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2012 Uninett AS
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
"""Utility functions for ipdevpoll."""

import logging
import re
from typing import TYPE_CHECKING

from IPy import IP

from twisted.internet import defer
from twisted.internet.defer import Deferred
from twisted.internet import reactor

from nav.oids import get_enterprise_id
from nav.enterprise.ids import VENDOR_ID_CISCOSYSTEMS
from nav.enterprise.ids import VENDOR_ID_ARUBA_NETWORKS_INC

if TYPE_CHECKING:
    from nav.mibs.bridge_mib import MultiBridgeMib

_logger = logging.getLogger(__name__)
MAX_MAC_ADDRESS_LENGTH = 6


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

    If the binary string exceeds 6 octets, only the last 6 octets are
    converted. If the string contains less than 6 octets the result will be
    padded with leading zeros.

    """
    if binary_mac:
        binary_mac = binary_mac[-6:].rjust(MAX_MAC_ADDRESS_LENGTH, b'\x00')
        return ":".join("%02x" % x for x in binary_mac)


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
    for pfx in prefix_list:
        sub = IP(pfx.net_address)
        if ip in sub:
            # Return the most precise prefix, ie the longest prefix
            if not ret or IP(ret.net_address).prefixlen() < sub.prefixlen():
                ret = pfx
    return ret


def is_invalid_database_string(string):
    """Returns True if string cannot be stored in PostgreSQL in its current
    representation. I.e. if string contains NUL characters, or is a binary object
    that cannot be decoded as UTF-8, or is another type of object, it is considered
    invalid.
    """
    return (isinstance(string, str) and "\x00" in string) or is_invalid_utf8(string)


def is_invalid_utf8(string):
    """Returns True if string is invalid UTF-8.

    If string is not a an str object, or is decodeable as UTF-8, False is
    returned.

    """
    if isinstance(string, bytes):
        try:
            string.decode('utf-8')
        except UnicodeDecodeError:
            return True
    return False


def log_unhandled_failure(logger, failure, msg, *args, **kwargs):
    """Logs a Failure with traceback using logger.

    If the logger has an effective loglevel of debug, a verbose traceback
    (complete with stack frames) is logged.  Otherwise, a regular traceback is
    loggged.

    """
    detail = 'default'
    if logger.isEnabledFor(logging.DEBUG):
        detail = 'verbose'
    traceback = failure.getTraceback(detail=detail)
    args = args + (traceback,)

    logger.error(msg + "\n%s", *args, **kwargs)


async def get_multibridgemib(agentproxy) -> "MultiBridgeMib":
    """Returns a MultiBridgeMib retriever pre-populated with instances from
    get_dot1d_instances()

    """
    from nav.mibs.bridge_mib import MultiBridgeMib

    instances = await get_dot1d_instances(agentproxy)
    return MultiBridgeMib(agentproxy, instances)


async def get_dot1d_instances(agentproxy):
    """
    Gets a list of alternative BRIDGE-MIB instances from a Cisco or Aruba
    agent.

    First

    :returns: A list of [(description, community), ...] for each alternate
              BRIDGE-MIB instance.

    """
    from nav.mibs.snmpv2_mib import Snmpv2Mib
    from nav.mibs.cisco_vtp_mib import CiscoVTPMib
    from nav.mibs.entity_mib import EntityMib

    enterprise_id = await (
        Snmpv2Mib(agentproxy).get_sysObjectID().addCallback(get_enterprise_id)
    )
    if enterprise_id == VENDOR_ID_CISCOSYSTEMS:
        mibclasses = [EntityMib, CiscoVTPMib]
        modifier = lambda x: x
    elif enterprise_id == VENDOR_ID_ARUBA_NETWORKS_INC:
        mibclasses = [EntityMib]
        modifier = _workaround_broken_aruba_alternate_communities
    else:
        mibclasses = []

    for mibclass in mibclasses:
        mib = mibclass(agentproxy)
        instances = await mib.retrieve_alternate_bridge_mibs()
        if instances:
            result = modifier(instances)
            modified_by = modifier if instances != result else None
            _logger.debug(
                "get_dot1d_instances(%r) [modified=%r]: %r",
                agentproxy.ip,
                modified_by,
                result,
            )
            return result

    return []


@defer.inlineCallbacks
def get_arista_vrf_instances(agentproxy) -> Deferred:
    """
    Gets a list of alternative VRF instances from an Arista agent

    :returns: A list of [(description, community), ...] for each alternate
              VRF

    """
    from nav.mibs.arista_vrf_mib import AristaVrfMib

    vrf_mib = AristaVrfMib(agentproxy)
    states = yield vrf_mib.get_vrf_states(only='active')
    vrfs = [('', agentproxy.community)]
    vrfs.extend((vrf, f"{agentproxy.community}@{vrf}") for vrf in states)
    return vrfs


_VLAN_RE = re.compile('^vlan([0-9]+)', re.IGNORECASE)


def _workaround_broken_aruba_alternate_communities(instances):
    """
    Works around a b0rked alternate bridge mib instance list from Aruba
    switches.

    Aruba switches tend to return the wrong community for BRIDGE-MIB instances
    from ENTITY-MIB::entLogicalCommunity - the community is not indexed for
    the given vlan.

    """
    output = []
    for name, community in instances:
        match = _VLAN_RE.match(name)
        if match:
            vlan = match.group(1)
            index = '@' + vlan
            if not community.endswith(index):
                community = community + index
        output.append((name, community))
    return output
