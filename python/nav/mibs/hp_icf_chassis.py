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

class HpIcfChassis(mibretriever.MibRetriever):
    from nav.smidumps.hp_icf_chassis import MIB as mib

    def __init__(self, agent_proxy):
        """Good old constructor..."""
        super(HpIcfChassis, self).__init__(agent_proxy)
        self.entity_mib = EntityMib(self.agent_proxy)
        self.sensor_table = None

    @defer.inlineCallbacks
    def _get_named_table(self, table_name):
        """Retrieve a table with the given name."""
        df = self.retrieve_table(table_name)
        df.addCallback(self.entity_mib.translate_result)
        ret_table = yield df
        named_table = EntityTable(ret_table)
        defer.returnValue(named_table)

    @defer.inlineCallbacks
    def get_sensor_entry_table(self):
        """ Get the table hpicfSensorEntry"""
        table = yield self._get_named_table('hpicfSensorTable')
        defer.returnValue(table)

    @defer.inlineCallbacks
    def _get_sensor_status(self, idx):
        is_up = False
        if not self.sensor_table:
            self.sensor_table = yield self.get_sensor_entry_table()
        sensor_row = self.sensor_table.get(idx, None)
        self._logger.error('sensor_row: %s' % sensor_row)
        if sensor_row:
            sensor_status = sensor_row.get('hpicfSensorStatus', None)
            if sensor_status:
                is_up = ((sensor_status == 4) or (sensor_status == 5))
        defer.returnValue(is_up)

    @defer.inlineCallbacks
    def is_fan_up(self, idx):
        is_up = yield self._get_sensor_status(idx)
        defer.returnValue(is_up)

    @defer.inlineCallbacks
    def is_psu_up(self, idx):
        is_up = yield self._get_sensor_status(idx)
        defer.returnValue(is_up)

    def get_oid_for_fan_status(self, idx):
        oid = None
        sensor_status_oid = self.nodes.get('hpicfSensorStatus', None)
        if sensor_status_oid:
            oid = '%s.%d' %(str(sensor_status_oid.oid), idx)
        return oid

    def get_oid_for_psu_status(self, idx):
        return self.get_oid_for_fan_status(idx)
