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
"LLDP-MIB handling"
import socket

from IPy import IP
from twisted.internet import defer

from nav.namedtuple import namedtuple
from nav.mibs import mibretriever
from nav.ipdevpoll.utils import get_multibridgemib, binary_mac_to_hex

class LLDPMib(mibretriever.MibRetriever):
    "A MibRetriever for handling LLDP-MIB"
    from nav.smidumps.lldp_mib import MIB as mib

    @defer.inlineCallbacks
    def get_remote_last_change(self):
        """Retrieves the sysUpTime value of the last time the lldpRemTable was
        changed.

        """
        oid = self.nodes['lldpStatsRemTablesLastChangeTime'].oid
        result = yield self.agent_proxy.walk(str(oid))
        for key, value in result.items():
            if oid.is_a_prefix_of(key):
                defer.returnValue(value)

    @defer.inlineCallbacks
    def get_remote_table(self):
        "Returns the contents of the lldpRemTable"
        table = yield self._retrieve_rem_table()
        if table:
            baseports = yield self._get_baseport_map()
        else:
            baseports = {}

        result = [self._rem_entry_to_neighbor(row, baseports)
                  for row in table.values()]
        defer.returnValue(result)

    def _retrieve_rem_table(self):
        return self.retrieve_columns([
                'lldpRemChassisIdSubtype',
                'lldpRemChassisId',
                'lldpRemPortIdSubtype',
                'lldpRemPortId',
                'lldpRemPortDesc',
                'lldpRemSysName',
                ]).addCallback(self.translate_result)

    @defer.inlineCallbacks
    def _get_baseport_map(self):
        bridge = yield get_multibridgemib(self.agent_proxy)
        baseports = yield bridge.get_baseport_ifindex_map()
        defer.returnValue(baseports)

    @staticmethod
    def _rem_entry_to_neighbor(row, baseports):
        _timemark, local_portnum, _index = row[0]

        # according to LLDP-MIB, lldpPortNumber is a baseport number on 802.1d
        # and 802.1q devices, otherwise it is an InterfaceIndex. The baseport
        # map is only found on 1D and 1Q devices, so we remap the
        # lldpPortNumber to an InterfaceIndex if we got an actual baseport map
        if local_portnum in baseports:
            local_portnum = baseports[local_portnum]

        chassis_id = IdSubtypes.get(row['lldpRemChassisIdSubtype'],
                                    row['lldpRemChassisId'])
        port_id = IdSubtypes.get(row['lldpRemPortIdSubtype'],
                                 row['lldpRemPortId'])

        return LLDPNeighbor(local_portnum, chassis_id, port_id,
                            row['lldpRemPortDesc'],
                            row['lldpRemSysName'])

# pylint: disable=C0103
LLDPNeighbor = namedtuple("LLDPNeighbor",
                          "ifindex chassis_id port_id port_desc sysname")

#
# A bunch of classes to define and help parse the various subtypes of remote
# chassis and port identifiers that may be used in the lldpRemTable.
#

# pylint: disable=C0111,C0103,R0904,R0903
class IdType(str):
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__,
                           str(self))

class MacAddress(IdType):
    def __new__(cls, *args, **kwargs):
        arg = args[0]
        if isinstance(arg, basestring):
            arg = binary_mac_to_hex(arg)
        elif isinstance(arg, cls):
            return arg
        return IdType.__new__(cls, arg)

class NetworkAddress(IdType):
    IPV4 = 1
    IPV6 = 2
    ADDR_FAMILY = {
        IPV4: socket.AF_INET,
        IPV6: socket.AF_INET6
        }

    def __new__(cls, *args, **kwargs):
        arg = args[0]
        if isinstance(arg, basestring):
            addr_type = ord(arg[0])
            addr_string = arg[1:]
            if addr_type in cls.ADDR_FAMILY:
                try:
                    ipstring = socket.inet_ntop(cls.ADDR_FAMILY[addr_type],
                                                addr_string)
                    arg = IP(ipstring)
                except (socket.error, ValueError):
                    pass
        elif isinstance(arg, cls):
            return arg
        return IdType.__new__(cls, arg)

# pylint: disable=C0111,C0103,R0904,R0903
class IdSubtypes(object):
    @classmethod
    def get(cls, typename, value):
        if typename:
            typeclass = getattr(cls, typename, str)
            return typeclass(value)
        else:
            return value

    class chassisComponent(IdType):
        pass

    class interfaceAlias(IdType):
        pass

    class portComponent(IdType):
        pass

    class macAddress(MacAddress):
        pass

    class networkAddress(NetworkAddress):
        pass

    class interfaceName(IdType):
        pass

    class local(IdType):
        pass

    class agentCircuitId(IdType):
        pass
