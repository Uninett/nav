#
# Copyright 2008 - 2011 (C) Uninett AS
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
"""Implements a wrapper around HpIcfFanMib- and HpIcfPowerSupplyMib-classes.
This is more convenient than calling both.

The reason why it is implemented this way is that the classes are operating
on two different MIBs,- and we need to keep them apart.  Therfore it is not
possible to use inheritance.  Call it cheating,- well it works perfectly...
"""

from nav.smidumps import get_mib
from nav.mibs import mibretriever

from nav.mibs.hpicf_fan_mib import HpIcfFanMib
from nav.mibs.hpicf_powersupply_mib import HpIcfPowerSupplyMib


class HpEntityFruControlMib(mibretriever.MibRetriever):
    """Actually a wrapper class around two classes that retrieve status
    for powersupplies and fans in HP netboxes."""
    mib = get_mib('POWERSUPPLY-MIB')

    def __init__(self, agent_proxy):
        """A good old constructor."""
        super(HpEntityFruControlMib, self).__init__(agent_proxy)
        self.hpicf_fan_mib = HpIcfFanMib(agent_proxy)
        self.hpicf_powersupply_mib = HpIcfPowerSupplyMib(agent_proxy)

    def is_fan_up(self, idx):
        """A wrapper for HpIcfFanMib.is_fan_up"""
        return self.hpicf_fan_mib.is_fan_up(idx)

    def get_oid_for_fan_status(self, idx):
        """A wrapper for HpIcfFanMib.get_oid_for_fan_status"""
        return self.hpicf_fan_mib.get_oid_for_fan_status(idx)

    def is_psu_up(self, idx):
        """A wrapper for HpIcfPowerSupplyMib.is_psu_up"""
        return self.hpicf_powersupply_mib.is_psu_up(idx)

    def get_oid_for_psu_status(self, idx):
        """A wrapper for HpIcfPowerSupplyMib.get_oid_for_psu_status"""
        return self.hpicf_powersupply_mib.get_oid_for_psu_status(idx)
