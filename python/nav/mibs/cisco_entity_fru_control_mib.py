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
from twisted.internet import defer

from nav.mibs import reduce_index
from nav.mibs import mibretriever

from nav.mibs.entity_mib import EntityMib
from nav.mibs.entity_mib import EntityTable

class CiscoEntityFruControlMib(mibretriever.MibRetriever):
    from nav.smidumps.cisco_entity_fru_control_mib import MIB as mib

    def __init__(self, agent_proxy):
        """Good old constructor...."""
        super(CiscoEntityFruControlMib, self).__init__(agent_proxy)
        self.entity_mib = EntityMib(self.agent_proxy)
        self.fantray_status_table = None

    def get_module_name(self):
        """return the MIB-name."""
        return self.mib.get('moduleName', None)

    @defer.inlineCallbacks
    def get_fan_status_table(self):
        """Retrieve the whole table of fan-sensors."""
        if not self.fantray_status_table:
            df = self.retrieve_table('cefcFanTrayStatusTable')
            df.addCallback(self.entity_mib.translate_result)
            status_table = yield df
            self.fantray_status_table = EntityTable(status_table)
        defer.returnValue(self.fantray_status_table)

    @defer.inlineCallbacks
    def is_fan_up(self, idx):
        """Return operation-status for fan with the given index."""
        fan_status_table = yield self.get_fan_status_table()
        fan_status_row = fan_status_table.get(idx, None)
        if fan_status_row:
            fan_status = fan_status_row.get('cefcFanTrayOperStatus', None)
            if fan_status:
                defer.returnValue((fan_status == 2))
        defer.returnValue(False)
    
    def get_oid_for_fan_status(self, idx):
        oid = None
        oper_status_oid = self.nodes.get('cefcFanTrayOperStatus').oid
        if oper_status_oid:
            oid = '%s.%d' % (str(oper_status_oid), idx)
        return oid
