#
# Copyright (C) 2009, 2012, 2013, 2016 Uninett AS
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
from twisted.internet import defer

from nav.bitvector import BitVector
from nav.smidumps import get_mib
from . import mibretriever

CHARS_IN_1024_BITS = 128


class CiscoVTPMib(mibretriever.MibRetriever):
    mib = get_mib('CISCO-VTP-MIB')

    @defer.inlineCallbacks
    def get_trunk_native_vlans(self):
        """Get a mapping of the native VLANs of trunk ports."""
        trunkports = yield self.retrieve_columns(
            ('vlanTrunkPortNativeVlan', 'vlanTrunkPortDynamicState')
        ).addCallback(self.translate_result)

        result = {
            index[0]: row['vlanTrunkPortNativeVlan']
            for index, row in trunkports.items()
            if row['vlanTrunkPortDynamicState'] in ('on', 'onNoNegotiate')
        }
        return result

    @defer.inlineCallbacks
    def get_trunk_enabled_vlans(self, as_bitvector=False):
        """Get a list of enabled VLANs for each trunk port.

        If as_bitvector=True, the result will be a raw BitVector object.

        """

        def get_vlan_list(row):
            concatenated_bits = b''
            for column in (
                'vlanTrunkPortVlansEnabled',
                'vlanTrunkPortVlansEnabled2k',
                'vlanTrunkPortVlansEnabled3k',
                'vlanTrunkPortVlansEnabled4k',
            ):
                value = row[column] or b''
                concatenated_bits += value.ljust(CHARS_IN_1024_BITS, b'\x00')

            enabled = BitVector(concatenated_bits)
            return as_bitvector and enabled or enabled.get_set_bits()

        trunkports = yield self.retrieve_columns(
            (
                'vlanTrunkPortVlansEnabled',
                'vlanTrunkPortDynamicState',
                'vlanTrunkPortVlansEnabled2k',
                'vlanTrunkPortVlansEnabled3k',
                'vlanTrunkPortVlansEnabled4k',
            )
        ).addCallback(self.translate_result)

        result = {
            index[0]: get_vlan_list(row)
            for index, row in trunkports.items()
            if row['vlanTrunkPortDynamicState'] in ('on', 'onNoNegotiate')
        }
        return result

    @defer.inlineCallbacks
    def get_ethernet_vlan_states(self):
        """Retrieves the state of each ethernet VLAN on the device"""
        states = yield self.retrieve_columns(
            ['vtpVlanState', 'vtpVlanType']
        ).addCallback(self.translate_result)

        result = {
            vlan: row['vtpVlanState']
            for (_domain, vlan), row in states.items()
            if row['vtpVlanType'] == 'ethernet'
        }
        return result

    @defer.inlineCallbacks
    def get_operational_vlans(self):
        """Retrieves a set of operational ethernet VLANs on this device"""
        states = yield self.get_ethernet_vlan_states()
        return set(vlan for vlan, state in states.items() if state == 'operational')

    @defer.inlineCallbacks
    def retrieve_alternate_bridge_mibs(self):
        """Retrieve a list of alternate bridge mib instances.

        :returns: A list of (descr, community) tuples for each operational
                  VLAN on this device.

        """
        vlans = yield self.get_operational_vlans()
        community = self.agent_proxy.community
        return [("vlan%s" % vlan, "%s@%s" % (community, vlan)) for vlan in vlans]
