#
# Copyright (C) 2013 Uninett AS
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
"""pynetsnmp specific trap agent functions."""

import select
import logging
from socket import AF_INET, AF_INET6, inet_ntop
from errno import EINTR
from ctypes import c_ushort, c_char, POINTER, cast, c_long

from IPy import IP
from pynetsnmp import netsnmp

from nav.errors import GeneralException
from nav.oids import OID
from nav.util import address_to_string

from .trap import SNMPTrap

__all__ = ['TrapListener', 'UnsupportedSnmpVersionError']

_logger = logging.getLogger(__name__)


class TrapListener(object):
    """A pynetsnmp based implementation of a TrapListener"""

    def __init__(self, *addresses):
        """Initializes a TrapListener.

        iface -- A (srcadr, port) tuple.

        """
        self.addresses = addresses
        self._client_callback = None
        self._sessions = [TrapSession(addr, self.callback) for addr in addresses]

    def open(self):
        """Opens the server socket at port 162."""
        for session in self._sessions:
            session.await_traps()

    def close(self):
        """Closes the server socket."""
        for session in self._sessions:
            session.close()

    def listen(self, _community, callback):
        """Listens for and dispatches incoming traps to callback.

        Any exceptions that occur, except SystemExit, are logged and
        subsequently ignored to avoid taking down the entire snmptrapd
        process by accident.

        """
        self._client_callback = callback
        while 1:
            fdlist, timeout = netsnmp.snmp_select_info()
            try:
                rlist, _wlist, _xlist = select.select(fdlist, [], [], timeout)
            except select.error as error:
                if error.args[0] == EINTR:
                    continue
                else:
                    raise
            if rlist:
                for fdescr in rlist:
                    netsnmp.snmp_read(fdescr)
            else:
                netsnmp.lib.snmp_timeout()

    def callback(self, src, pdu):
        """Handles trap callbacks from a TrapSession"""
        if not self._client_callback:
            return

        agent_addr = None
        generic_type = None
        community = pdu.community[: pdu.community_len]

        varbinds = netsnmp.getResult(pdu, _logger)

        if pdu.version == netsnmp.SNMP_VERSION_1:
            version = 1
            agent_addr = ".".join(str(d) for d in pdu.agent_addr)
            snmp_trap_oid, generic_type = transform_trap_type(pdu)
            uptime = pdu.time
        elif pdu.version == netsnmp.SNMP_VERSION_2c:
            version = 2
            _time_oid, time_val = varbinds.pop(0)
            _trap_oid_oid, trap_oid = varbinds.pop(0)

            uptime = time_val
            snmp_trap_oid = OID(trap_oid)
        else:
            raise UnsupportedSnmpVersionError(pdu.version)

        # Dump varbinds to debug log
        _logger.debug("varbinds: %r", varbinds)
        # Add remaining varbinds to dict
        varbind_dict = dict(
            (str(OID(oid)), value_to_str(value)) for oid, value in varbinds
        )

        trap = SNMPTrap(
            str(src),
            agent_addr or str(src),
            None,
            generic_type,
            str(snmp_trap_oid),
            uptime,
            community,
            version,
            varbind_dict,
        )
        self._client_callback(trap)


def value_to_str(value):
    """Converts a value from a varbind to a string, as that is what the
    SNMPTrap API expects :-P
    """
    if isinstance(value, tuple):
        return str(OID(value))
    elif isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            pass

    return str(value)


SNMP_TRAPS = OID('.1.3.6.1.6.3.1.1.5')
TRAP_MAP = {
    netsnmp.SNMP_TRAP_COLDSTART: 'coldStart',
    netsnmp.SNMP_TRAP_WARMSTART: 'warmStart',
    netsnmp.SNMP_TRAP_LINKDOWN: 'linkDown',
    netsnmp.SNMP_TRAP_LINKUP: 'linkUp',
    netsnmp.SNMP_TRAP_AUTHFAIL: 'authenticationFailure',
    netsnmp.SNMP_TRAP_EGPNEIGHBORLOSS: 'egpNeighborLoss',
    netsnmp.SNMP_TRAP_ENTERPRISESPECIFIC: 'enterpriseSpecific',
}


def transform_trap_type(pdu):
    """Transforms trap information from an SNMP-v1 pdu to something that
    is consistent with SNMP-v2c, as documented in RFC2576.

    :returns: A tuple of (snmpTrapOID, genericType)

    """
    enterprise_type = POINTER(c_long * pdu.enterprise_length)
    enterprise_p = cast(pdu.enterprise, enterprise_type)
    enterprise = OID(enterprise_p.contents)

    generic = pdu.trap_type

    # According to RFC2576 "Coexistence between Version 1, Version 2,
    # and Version 3 of the Internet-standard Network Management
    # Framework", we build snmpTrapOID from the snmp-v1 trap by
    # combining enterprise + 0 + specific trap parameter IF the
    # generic trap parameter is 6. If not, the traps are defined as
    # 1.3.6.1.6.3.1.1.5 + (generic trap parameter + 1)
    if generic == netsnmp.SNMP_TRAP_ENTERPRISESPECIFIC:
        snmp_trap_oid = enterprise + [0, pdu.specific_type]
    else:
        snmp_trap_oid = SNMP_TRAPS + [generic + 1]

    generic_type = TRAP_MAP.get(generic, str(generic)).upper()
    return snmp_trap_oid, generic_type


class TrapSession(netsnmp.Session):
    """A shim to adapt netsnmp.Session to our trap-receiving needs"""

    def __init__(self, iface, callback):
        super(TrapSession, self).__init__()
        self.addr, self.port = iface
        self._callback = callback

    def await_traps(self):
        """Starts dispatch of incoming traps to the registered callback"""
        addr = address_to_string(self.addr, self.port)
        if IP(self.addr).version() == 6:
            tdomain = 'udp6:'
            self._initv6()
        else:
            tdomain = "udp:"
        return self.awaitTraps((tdomain + addr))

    def _initv6(self):
        lib = netsnmp.lib
        sentinel = object()
        if getattr(lib, "netsnmp_udpipv6_ctor", sentinel) is not sentinel:
            lib.netsnmp_udpipv6_ctor()
        elif getattr(lib, "netsnmp_udp6_ctor", sentinel) is not sentinel:
            lib.netsnmp_udp6_ctor()
        else:
            _logger.warning(
                "Cannot find constructor function for UDP/IPv6 transport domain object."
            )

    def callback(self, pdu):
        addr = get_transport_addr(pdu)
        self._callback(addr, pdu)


IPADDR_SIZE = 4
IP6ADDR_SIZE = 16
IPADDR_OFFSET = 4
IP6ADDR_OFFSET = 8


def get_transport_addr(pdu):
    """Retrieves the IP source address from the PDU's reference to an opaque
    transport data struct.

    Only works when assuming the opaque structure is sockaddr_in and
    sockaddr_in6. It should be as long as we are only using an IPv4 or
    IPv6-based netsnmp transport.

    """
    if pdu.transport_data_length <= 1:
        return

    # peek the first two bytes of the pdu's transport data to determine socket
    # address family (we are assuming the transport_data is a sockaddr_in or
    # sockaddr_in6 structure and accessing it naughtily here)
    family_p = cast(pdu.transport_data, POINTER(c_ushort))
    family = family_p.contents.value
    if family not in (AF_INET, AF_INET6):
        return

    addr_size, offset = (
        (IPADDR_SIZE, IPADDR_OFFSET)
        if family == AF_INET
        else (IP6ADDR_SIZE, IP6ADDR_OFFSET)
    )

    buffer_type = c_char * pdu.transport_data_length
    data_p = cast(pdu.transport_data, POINTER(buffer_type))
    data = data_p.contents
    addr = data[offset : offset + addr_size]
    return inet_ntop(family, addr)


class UnsupportedSnmpVersionError(GeneralException):
    """Received a trap with an unsupported SNMP version"""

    pass
