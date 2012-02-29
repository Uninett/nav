#
# Copyright (C) 2009, 2011 UNINETT AS
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
"""Implements a Q-BRIDGE-MIB MibRetriever and associated functionality."""
from twisted.internet import defer

import nav.bitvector
from nav.mibs import mibretriever, reduce_index

class QBridgeMib(mibretriever.MibRetriever):
    from nav.smidumps.qbridge_mib import MIB as mib

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
        return df.addCallback(convert_data_to_portlist)

    def get_vlan_current_untagged_ports(self):
        """Retrieves, for each VLAN, a list of ports that can currently
        transmit untagged frames for the VLAN.

        :returns: A Deferred, whose result is a dict of the form
                  { PVID: <PortList instance> }

        """
        df = self.retrieve_column('dot1qVlanCurrentUntaggedPorts')
        df.addCallback(filter_newest_current_entries)
        return df.addCallback(convert_data_to_portlist)

    def get_vlan_static_egress_ports(self):
        """Retrieves, for each VLAN, a list of ports that are configured to
        transmit untagged frames for the VLAN.

        :returns: A Deferred, whose result is a dict of the form
                  { PVID: <PortList instance> }

        """
        df = self.retrieve_column('dot1qVlanStaticEgressPorts')
        df.addCallback(reduce_index)
        return df.addCallback(convert_data_to_portlist)


    def get_vlan_static_untagged_ports(self):
        """Retrieves, for each VLAN, a list of ports that are configured to
        transmit untagged frames for the VLAN.

        :returns: A Deferred, whose result is a dict of the form
                  { PVID: <PortList instance> }

        """
        df = self.retrieve_column('dot1qVlanStaticUntaggedPorts')
        df.addCallback(reduce_index)
        return df.addCallback(convert_data_to_portlist)

    @defer.inlineCallbacks
    def get_forwarding_database(self):
        "Retrieves the forwarding databases of the device"
        columns = yield self.retrieve_columns(['dot1qTpFdbPort',
                                               'dot1qTpFdbStatus'])
        columns = self.translate_result(columns)
        learned = (row for row in columns.values()
                   if row['dot1qTpFdbStatus'] == 'learned')
        result = []
        for row in learned:
            index = row[0]
            _fdb_id = index[0]
            mac = index[1:]
            mac =  ':'.join("%02x" % o for o in mac[-6:])
            port = row['dot1qTpFdbPort']
            result.append((mac, port))
        defer.returnValue(result)

def filter_newest_current_entries(dot1qvlancurrenttable):
    """Filters a result from the dot1qVlanCurrentTable, removing the
    TimeFilter element of the table index and returning only the newest entry
    for each VLAN.

    """
    return dict((vlan_index, data)
                for (time_index, vlan_index), data
                in sorted(dot1qvlancurrenttable.items()))

def convert_data_to_portlist(result):
    return dict((key, PortList(data))
                 for key, data in result.items())

class PortList(str):
    """Represent an octet string, as defined by the PortList syntax of
    the Q-BRIDGE-MIB.

    Offers conveniences such as subtracting one PortList from another,
    and retrieving a list of port numbers represented by a PortList
    octet string.

    """

    def __sub__(self, other):
        # pad other with zeros if it happens to be shorter than self
        padded_other = other.ljust(len(self), '\x00')
        new_ints = [ord(char) - ord(padded_other[index])
                    for index, char in enumerate(self)]
        return PortList(''.join(chr(i) for i in new_ints))

    def get_ports(self):
        """Return a list of port numbers represented by this PortList."""
        vector = nav.bitvector.BitVector(self)
        # a bitvector is indexed from 0, but ports are indexed from 1
        ports = [b+1 for b in vector.get_set_bits()]
        return ports
