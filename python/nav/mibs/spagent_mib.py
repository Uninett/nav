#
# Copyright (C) 2014 UNINETT
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
"""AKCP SPAGENT-MIB MibRetriever"""
from twisted.internet import defer
from nav.mibs import reduce_index
from nav.mibs.mibretriever import MibRetriever


class SPAgentMib(MibRetriever):
    """SPAGENT-MIB MibRetriever"""
    from nav.smidumps.spagent_mib import MIB as mib

    @defer.inlineCallbacks
    def get_all_sensors(self):
        result = yield self.retrieve_columns([
            'sensorProbeTempDescription',
            'sensorProbeTempOnline',
            'sensorProbeTempDegreeType',
        ]).addCallback(self.translate_result).addCallback(reduce_index)

        sensors = (self._temp_row_to_sensor(index, row)
                   for index, row in result.iteritems())

        defer.returnValue([s for s in sensors if s])

    def _temp_row_to_sensor(self, index, row):
        online = row.get('sensorProbeTempOnline', 'offline')
        if online == 'offline':
            return

        internal_name = 'temperature%s' % index
        descr = row.get('sensorProbeTempDescription', internal_name)

        mibobject = self.nodes.get('sensorProbeTempDegreeRaw')
        readout_oid = str(mibobject.oid) + str(index)

        unit = row.get("sensorProbeTempDegreeType", None)
        if unit == 'fahr':
            unit = 'fahrenheit'

        return {
            'oid': readout_oid,
            'unit_of_measurement': unit,
            'precision': 1,
            'scale': None,
            'description': descr,
            'name': descr,
            'internal_name': internal_name,
            'mib': 'SPAGENT-MIB',
        }
