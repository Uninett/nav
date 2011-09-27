#
# Copyright 2008 - 2011 (C) UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
"""

from nav.mibs import mibretriever

from nav.mibs.hpicf_fan_mib import HpIcfFanMib
from nav.mibs.hpicf_powersupply_mib import HpIcfPowerSupplyMib

class HpEntityFruControlMib(mibretriever.MibRetriever):
    from nav.smidumps.hpicf_powersupply_mib import MIB as mib

    def __init__(self, agent_proxy):
        super(HpEntityFruControlMib, self).__init__(agent_proxy)
        self.hpicf_fan_mib = HpIcfFanMib(agent_proxy)
        self.hpicf_powersupply_mib = HpIcfPowerSupplyMib(agent_proxy)

    def is_fan_up(self, idx):
        return self.hpicf_fan_mib.is_fan_up(idx)

    def get_oid_for_fan_status(self, idx):
        return self.hpicf_fan_mib.get_oid_for_fan_status(idx)

    def is_psu_up(self, idx):
        return self.hpicf_powersupply_mib.is_psu_up(idx)

    def get_oid_for_psu_status(self, idx):
        return self.hpicf_powersupply_mib.get_oid_for_psu_status(idx)
