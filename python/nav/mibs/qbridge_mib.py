#
# Copyright (C) 2009, 2011, 2012 Uninett AS
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
"""Implements a Q-BRIDGE-MIB MibRetriever and associated functionality."""

import re

from twisted.internet import defer

import nav.bitvector
from nav.smidumps import get_mib
from nav.mibs import mibretriever, reduce_index


class QBridgeMib(mibretriever.MibRetriever):
    mib = get_mib('Q-BRIDGE-MIB')

    juniper_hack = False

    def get_baseport_pvid_map(self):
        """Retrieves the mapping between baseport numbers and VLAN tag numbers.

        :returns: A Deferred whose result is a dict of the form
                  { baseportnum: PVID }

        """
        df = self.retrieve_column('dot1qPvid')
        return df.addCallback(reduce_index)

    def get_vlan_current_egress_ports(self):
        """Retrieves, for each VLAN, a list of ports that can currently
        transmit frames for the VLAN.

        :returns: A Deferred, whose result is a dict of the form
                  { PVID: <PortList instance> }

        """
        df = self.retrieve_column('dot1qVlanCurrentEgressPorts')
        df.addCallback(filter_newest_current_entries)
        return df.addCallback(convert_data_to_portlist, self.juniper_hack)

    def get_vlan_current_untagged_ports(self):
        """Retrieves, for each VLAN, a list of ports that can currently
        transmit untagged frames for the VLAN.

        :returns: A Deferred, whose result is a dict of the form
                  { PVID: <PortList instance> }

        """
        df = self.retrieve_column('dot1qVlanCurrentUntaggedPorts')
        df.addCallback(filter_newest_current_entries)
        return df.addCallback(convert_data_to_portlist, self.juniper_hack)

    def get_vlan_static_egress_ports(self):
        """Retrieves, for each VLAN, a list of ports that are configured to
        transmit frames for the VLAN.

        :returns: A Deferred, whose result is a dict of the form
                  { PVID: <PortList instance> }

        """
        df = self.retrieve_column('dot1qVlanStaticEgressPorts')
        df.addCallback(reduce_index)
        return df.addCallback(convert_data_to_portlist, self.juniper_hack)

    def get_vlan_static_untagged_ports(self):
        """Retrieves, for each VLAN, a list of ports that are configured to
        transmit untagged frames for the VLAN.

        :returns: A Deferred, whose result is a dict of the form
                  { PVID: <PortList instance> }

        """
        df = self.retrieve_column('dot1qVlanStaticUntaggedPorts')
        df.addCallback(reduce_index)
        return df.addCallback(convert_data_to_portlist, self.juniper_hack)

    @defer.inlineCallbacks
    def get_forwarding_database(self):
        "Retrieves the forwarding databases of the device"
        columns = yield self.retrieve_columns(['dot1qTpFdbPort', 'dot1qTpFdbStatus'])
        columns = self.translate_result(columns)
        valid = (
            row
            for row in columns.values()
            if row['dot1qTpFdbStatus'] not in ('self', 'invalid')
        )
        result = []
        for row in valid:
            index = row[0]
            mac = index[1:]
            mac = ':'.join("%02x" % o for o in mac[-6:])
            port = row['dot1qTpFdbPort']
            result.append((mac, port))
        return result

    @defer.inlineCallbacks
    def get_vlan_static_names(self):
        names = yield self.retrieve_column('dot1qVlanStaticName').addCallback(
            reduce_index
        )
        # Workaround for faulty SNMP agents: strip null bytes
        for key, value in names.items():
            if isinstance(value, str) and "\x00" in value:
                names[key] = value.replace("\x00", "")
        return names


def filter_newest_current_entries(dot1qvlancurrenttable):
    """Filters a result from the dot1qVlanCurrentTable, removing the
    TimeFilter element of the table index and returning only the newest entry
    for each VLAN.

    """
    return dict(
        (vlan_index, data)
        for (time_index, vlan_index), data in sorted(dot1qvlancurrenttable.items())
    )


def convert_data_to_portlist(result, juniper_hack):
    return {key: portlist(data, juniper_hack) for key, data in result.items()}


def portlist_spec(data):
    """Return a set of port numbers represented by this PortList."""
    vector = nav.bitvector.BitVector(data)
    # a bitvector is indexed from 0, but ports are indexed from 1
    return {b + 1 for b in vector.get_set_bits()}


def portlist_juniper(data):
    """Return a set of port numbers represented by this PortList
    interpreted in junipers strange notion of the spec or None if data
    does not match this format
    """
    # data would normally be binary, but since Juniper ignores the spec, it's a comma
    # separated ASCII string:
    if isinstance(data, bytes):
        try:
            data = data.decode('ascii')
        except UnicodeDecodeError:
            return None
    if re.match("^[0-9,]+$", data):
        return {int(x) for x in data.split(",")}
    return None


def portlist(data, juniper_hack=False):
    """Return a set of port numbers represented by this PortList.

    If juniper_hack is true and it is formatted according to junipers
    formatting, interpret it that way, otherwise follow the spec
    """
    if not juniper_hack:
        return portlist_spec(data)
    juniper_list = portlist_juniper(data)
    if not juniper_list:
        return portlist_spec(data)
    return juniper_list
