# encoding: utf-8
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

from nav.mibs.entity_mib import EntityTable

class HpIcfPowerSupplyMib(mibretriever.MibRetriever):
    from nav.smidumps.hpicf_powersupply_mib import MIB as mib

    def __init__(self, agent_proxy):
        super(HpIcfPowerSupplyMib, self).__init__(agent_proxy)
        self.psu_status_table = None

    @defer.inlineCallbacks
    def _get_psu_status_table(self):
        df = self.retrieve_table('hpicfPsTable')
        df.addCallback(self.translate_result)
        df.addCallback(reduce_index)
        psu_table = yield df
        self._logger.error('psu_table: %s' % psu_table)
        defer.returnValue(psu_table)

    def _get_psu_status(self, psu_status):
        status = 'n'
        if (psu_status == 'psNotPresent'
                or psu_status == 'psNotPlugged'
                     or psu_status == 'psPowered'):
            status = 'y'
        elif psu_status == 'psFailed' or psu_status == 'psPermFailure':
            status = 'n'
        elif psu_status == 'psMax':
            status = 'w'
        return status

    @defer.inlineCallbacks
    def is_psu_up(self, idx):
        is_up = None
        if not self.psu_status_table:
            self.psu_status_table = yield self._get_psu_status_table()
        psu_status_row = self.psu_status_table.get(idx, None)
        if psu_status_row:
            psu_status = psu_status_row.get('hpicfPsState', None)
            if psu_status:
                is_up = self._get_psu_status(psu_status)
        defer.returnValue(is_up)
            
    def get_oid_for_psu_status(self, idx):
        oid = None
        psu_state_oid = self.nodes.get('hpicfPsState', None)
        if psu_state_oid:
            oid = '%s.%d' % (str(psu_state_oid.oid), idx)
        return oid
