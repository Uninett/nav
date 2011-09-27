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

class HpIcfFanMib(mibretriever.MibRetriever):
    from nav.smidumps.hpicf_fan_mib import MIB as mib
    
    def __init__(self, agent_proxy):
        super(HpIcfFanMib, self).__init__(agent_proxy)
        self.fan_status_table = None

    @defer.inlineCallbacks
    def _get_fan_status_table(self):
        df = self.retrieve_table('hpicfFanTable')
        df.addCallback(self.translate_result)
        df.addCallback(reduce_index)
        fan_table = yield df
        self._logger.error('fan_table: %s' % fan_table)
        defer.returnValue(fan_table)
        
    def _get_fan_status(self, fan_status):
        status = 'n'
        if fan_status == 'failed':
            status = 'n'
        elif fan_status == 'removed' or fan_status == 'off':
            status = 'y'
        elif (fan_status == 'underspeeed'
                    or fan_status == 'overspeed'
                        or fan_status == 'maxstate'):
            status = 'w'
        elif fan_status == 'ok':
            status = 'y'
        return status

    @defer.inlineCallbacks
    def is_fan_up(self, idx):
        is_up = None
        if not self.fan_status_table:
            self.fan_status_table = yield self._get_fan_status_table()
        fan_status_row = self.fan_status_table.get(idx, None)
        if fan_status_row:
            fan_status = fan_status_row.get('hpicfFanState', None)
            if fan_status:
                is_up = self._get_fan_status(fan_status)
        defer.returnValue(is_up)

    def get_oid_for_fan_status(self, idx):
        oid = None
        fan_state_oid = self.nodes.get('hpicfFanState', None)
        if fan_state_oid:
            oid = '%s.%d' % (str(fan_state_oid.oid), idx)
        return oid
