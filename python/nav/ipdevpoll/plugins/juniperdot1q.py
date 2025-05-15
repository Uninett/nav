#
# Copyright (C) 2016 Uninett AS
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
"""ipdevpoll plugin to collect 802.1q VLAN information, but with a workaround
for Juniper's moronic munging of VLAN tags in the Q-BRIDGE-MIB.

"What's that", you say? Well, Juniper has their own creative interpretation
of the Q-BRIDGE-MIB (RFC 4363). They think they can omit real VLAN tags as
identifiers in the MIB, and use some opaque internal identifier instead. To
find out which actual VLAN tag the identifier represents, you will need to
consult a mapping in the proprietary JUNIPER-VLAN-MIB.

The really funny part is that, when first discovered, this was reported as a
bug against Q-BRIDGE-MIB::dot1qPvid (Which NAV basically uses to find the
native/untagged VLAN of each switch port) - Juniper admitted that this was a
mistake and fixed the bug, so now, dot1qPvid reports actual VLAN tags.
However, when the same problem was discovered and reported for
dot1qVlanStaticTable (which NAV uses to discover which ports are tagged on
each VLAN), Juniper refused to admit that their interpretation of the MIB was
wrong, and now keep munging that table's index by using opaque, internal
identifiers. So Juniper devs are morons. Who knew?

The following can be used as proof of stupidity^W^W^W reference material:
https://www.juniper.net/documentation/en_US/junos12.3/topics/reference/general/snmp-ex-vlans-retrieving.html

"""

from twisted.internet.defer import inlineCallbacks
from nav.enterprise.ids import VENDOR_ID_JUNIPER_NETWORKS_INC
from nav.oids import OID
from . import dot1q

# F**k the MIB, let's do it commando-style with Juniper!
_jnxExVlanTag = '.1.3.6.1.4.1.2636.3.40.1.5.1.5.1.5'


class JuniperDot1q(dot1q.Dot1q):
    """Collect 802.1q info from BRIDGE and Q-BRIDGE MIBs, with Juniper patch"""

    def __init__(self, *args, **kwargs):
        super(JuniperDot1q, self).__init__(*args, **kwargs)
        self.jnx_vlan_map = {}
        if self.__is_a_moronic_juniper_device():
            self.qbridgemib.juniper_hack = True

    @inlineCallbacks
    def handle(self):
        if self.__is_a_moronic_juniper_device():
            self._logger.debug("Collecting Juniper VLAN mapping")
            self.jnx_vlan_map = yield self.__get_jnx_ex_vlan_tag()

        yield super(JuniperDot1q, self).handle()

    def _remap_vlan(self, vlan_ident):
        if self.jnx_vlan_map:
            try:
                return self.jnx_vlan_map[vlan_ident]
            except KeyError:
                self._logger.info(
                    "cannot map juniper vlan %s to a tag, using raw value",
                    vlan_ident,
                )

        return vlan_ident

    @inlineCallbacks
    def _retrieve_vlan_ports(self):
        """
        Overrides base class implementation to translate VLAN ids to VLAN
        tags on Juniper switches.

        """
        (egress, untagged) = yield super(JuniperDot1q, self)._retrieve_vlan_ports()
        if not self.jnx_vlan_map:
            return (egress, untagged)

        new_egress = {self._remap_vlan(key): value for key, value in egress.items()}
        new_untagged = {self._remap_vlan(key): value for key, value in untagged.items()}

        return (new_egress, new_untagged)

    def __is_a_moronic_juniper_device(self):
        if self.netbox.type:
            vendor_id = self.netbox.type.get_enterprise_id()
            if vendor_id == VENDOR_ID_JUNIPER_NETWORKS_INC:
                return True

    @inlineCallbacks
    def __get_jnx_ex_vlan_tag(self):
        result = yield self.agent.getTable([_jnxExVlanTag])
        mappings = result.get(_jnxExVlanTag, {})
        mappings = {OID(key)[-1]: value for key, value in mappings.items()}
        self._logger.debug("got jnxExVlanTag map: %r", mappings)
        return mappings
