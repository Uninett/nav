#
# Copyright (C) 2012, 2016 Uninett AS
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
""" "LLDP-MIB handling"""

import socket
from collections import namedtuple

from twisted.internet.defer import inlineCallbacks

from nav.ip import IP
from nav.mibs.if_mib import IfMib
from nav.smidumps import get_mib
from nav.mibs import mibretriever, reduce_index
from nav import macaddress


class LLDPMib(mibretriever.MibRetriever):
    """A MibRetriever for handling LLDP-MIB"""

    mib = get_mib('LLDP-MIB')

    def get_remote_last_change(self):
        """Retrieves the sysUpTime value of the last time the lldpRemTable was
        changed.

        """
        return self.get_next('lldpStatsRemTablesLastChangeTime')

    @inlineCallbacks
    def get_remote_table(self):
        """Returns the contents of the lldpRemTable"""
        table = yield self._retrieve_rem_table()
        if table:
            rows = yield self._translate_port_numbers(table)
            result = [self._remote_entry_to_neighbor(row) for row in rows]
        else:
            result = []

        return result

    def _retrieve_rem_table(self):
        return self.retrieve_columns(
            [
                'lldpRemChassisIdSubtype',
                'lldpRemChassisId',
                'lldpRemPortIdSubtype',
                'lldpRemPortId',
                'lldpRemPortDesc',
                'lldpRemSysName',
            ]
        ).addCallback(self.translate_result)

    @staticmethod
    def _remote_entry_to_neighbor(row):
        ifindex = row[0]

        chassis_id = IdSubtypes.get(
            row['lldpRemChassisIdSubtype'], row['lldpRemChassisId']
        )
        port_id = IdSubtypes.get(row['lldpRemPortIdSubtype'], row['lldpRemPortId'])

        return LLDPNeighbor(
            ifindex, chassis_id, port_id, row['lldpRemPortDesc'], row['lldpRemSysName']
        )

    @inlineCallbacks
    def _translate_port_numbers(self, remote_table):
        """
        Translates local port number references to ifIndexes in lldpRemTable
        result, if necessary.

        Ideally, we want all port references to be ifIndexes, but some devices'
        LLDP-MIB implementations will use dot1dBasePort references or something
        altogether different. In our experience, ifIndex is most common,
        dot1dBasePort is the second most common, while sometimes (such as in
        the case with Alcatel), some arbitrary internal number is used, but
        translateable into an ifIndex via the lldpLocPortTable.

        """
        if self._is_remote_table_index_broken(remote_table):
            self._logger.warning("lldpRemTable has broken row indexes on this device")
            return []

        remotes = remote_table.values()
        local_ports = yield self._retrieve_local_ports()

        # Use SNMP queries to make lookup tables, if necessary
        idtypes = set(type(port) for port in local_ports.values())
        if idtypes:
            self._logger.debug(
                "local port id types in use: %s", [t.__name__ for t in idtypes]
            )
        uses_ifnames = IdSubtypes.interfaceName in idtypes
        if uses_ifnames:
            self._logger.debug(
                "translation of local port numbers by ifName is necessary"
            )
            name_to_ifindex = yield self._make_interface_lookup_dict()
        else:
            name_to_ifindex = {}

        # Do the actual translations
        lookup = {}
        for local_portnum, port in local_ports.items():
            if isinstance(port, IdSubtypes.interfaceName):
                ifindex = name_to_ifindex.get(port, None)
                if ifindex:
                    self._logger.debug(
                        "translating local port num %s via %r to ifindex %s",
                        local_portnum,
                        port,
                        ifindex,
                    )
                    lookup[local_portnum] = ifindex
            elif (
                isinstance(port, IdSubtypes.local)
                and port.isdigit()
                and local_portnum != int(port)
            ):
                self._logger.debug(
                    "translating local port num %s to ifindex %s",
                    local_portnum,
                    port,
                )
                lookup[local_portnum] = int(port)

        for remote in remotes:
            _timemark, local_portnum, _index = remote[0]
            remote[0] = lookup.get(local_portnum, local_portnum)

        return remotes

    @staticmethod
    def _is_remote_table_index_broken(remote_table):
        """Returns True if an lldpRemTable response has a broken row index"""
        return any(len(row[0]) != 3 for row in remote_table.values())

    @inlineCallbacks
    def _retrieve_local_ports(self):
        ports = (
            yield self.retrieve_columns(
                [
                    'lldpLocPortIdSubtype',
                    'lldpLocPortId',
                ]
            )
            .addCallback(self.translate_result)
            .addCallback(reduce_index)
        )
        result = {
            index: IdSubtypes.get(row['lldpLocPortIdSubtype'], row['lldpLocPortId'])
            for index, row in ports.items()
        }
        return result

    @inlineCallbacks
    def _make_interface_lookup_dict(self):
        ifmib = IfMib(self.agent_proxy)
        ifnames = yield ifmib.get_ifnames()
        lookup = {}
        for ifindex, (ifname, ifdescr) in ifnames.items():
            lookup[ifdescr] = ifindex
            lookup[ifname] = ifindex
        return lookup


LLDPNeighbor = namedtuple(
    "LLDPNeighbor", "ifindex chassis_id port_id port_desc sysname"
)

#
# A bunch of classes to define and help parse the various subtypes of remote
# chassis and port identifiers that may be used in the lldpRemTable.
#


class IdType(str):
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, str(self))

    def isdigit(self):
        """Returns True if self can be successfully cast to an integer"""
        try:
            int(self)
            return True
        except ValueError:
            return False


class BinaryOrString(IdType):
    def __new__(cls, *args, **_kwargs):
        arg = args[0]
        if isinstance(arg, bytes):
            try:
                arg = arg.decode('utf-8')
            except (ValueError, UnicodeDecodeError):
                pass
        elif isinstance(arg, cls):
            return arg
        return IdType.__new__(cls, arg)


class MacAddress(IdType):
    def __new__(cls, *args, **_kwargs):
        arg = args[0]
        if isinstance(arg, bytes):
            try:
                arg = macaddress.MacAddress.from_octets(arg)
            except ValueError:
                arg = macaddress.MacAddress(arg.decode('utf-8'))
        elif isinstance(arg, cls):
            return arg
        return IdType.__new__(cls, arg)


class NetworkAddress(IdType):
    IPV4 = 1
    IPV6 = 2
    ADDR_FAMILY = {
        IPV4: socket.AF_INET,
        IPV6: socket.AF_INET6,
        bytes(IPV4): socket.AF_INET,
        bytes(IPV6): socket.AF_INET6,
    }

    def __new__(cls, *args, **_kwargs):
        arg = args[0]
        if arg and isinstance(arg, bytes):
            addr_type = arg[0]
            addr_string = arg[1:]
            if addr_type in cls.ADDR_FAMILY:
                try:
                    ipstring = socket.inet_ntop(cls.ADDR_FAMILY[addr_type], addr_string)
                    arg = IP(ipstring)
                except (socket.error, ValueError):
                    pass
        elif arg and isinstance(arg, cls):
            return arg
        return IdType.__new__(cls, arg)


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

    class interfaceAlias(BinaryOrString):
        pass

    class portComponent(IdType):
        pass

    class macAddress(MacAddress):
        pass

    class networkAddress(NetworkAddress):
        pass

    class interfaceName(BinaryOrString):
        pass

    class local(BinaryOrString):
        pass

    class agentCircuitId(IdType):
        pass
