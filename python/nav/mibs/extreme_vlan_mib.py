#
# Copyright (C) 2011 Uninett AS
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
"""Implements an EXTREME-VLAN-MIB MibRetriever"""

from nav.smidumps import get_mib
from nav.mibs.qbridge_mib import portlist
from nav.mibs import reduce_index
from . import mibretriever


class ExtremeVlanMib(mibretriever.MibRetriever):
    """Gets data from the EXTREME-VLAN-MIB"""

    mib = get_mib('EXTREME-VLAN-MIB')

    def get_vlan_ports(self):
        """Retrieves the VLAN port configurations.

        :returns: A dict of the form
                  { extremeVlanIfIndex: (tagged_portlist, untagged_portlist) }

        """
        df = self.retrieve_table('extremeVlanOpaqueTable')
        df.addCallback(_strip_slot_numbers_from_index)
        df.addCallback(_convert_columns_to_portlists)
        return df

    def get_ifindex_vlan_map(self):
        """Retrieves a mapping of ifIndexes to VLAN IDs.

        The Extreme switch will have a virtual interface for each active VLAN,
        this maps those interfaces' ifIndexes to their corresponding VLAN id.

        :returns: A dict of the form { ifindex: vlan_id }
        """
        df = self.retrieve_column('extremeVlanIfVlanId')
        return df.addCallback(reduce_index)


def _strip_slot_numbers_from_index(table):
    return dict((if_index, row) for (if_index, slot_number), row in table.items())


def _convert_columns_to_portlists(table):
    return dict(
        (
            key,
            (
                portlist(row['extremeVlanOpaqueTaggedPorts']),
                portlist(row['extremeVlanOpaqueUntaggedPorts']),
            ),
        )
        for key, row in table.items()
    )
