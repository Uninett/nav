#
# Copyright (C) 2013 Uninett AS
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
from django.utils.six import itervalues, iteritems
from twisted.internet import defer
from nav.mibs import mibretriever, reduce_index
from nav.mibs.entity_mib import EntityMib
from nav.oids import OID

PHYSICAL_INDEX = 'cpmCPUTotalPhysicalIndex'
TOTAL_5_MIN_REV = 'cpmCPUTotal5minRev'
TOTAL_1_MIN_REV = 'cpmCPUTotal1minRev'


class CiscoProcessMib(mibretriever.MibRetriever):
    from nav.smidumps.cisco_process_mib import MIB as mib

    @defer.inlineCallbacks
    def get_cpu_loadavg(self):
        load = yield self.retrieve_columns([
            PHYSICAL_INDEX,
            TOTAL_5_MIN_REV,
            TOTAL_1_MIN_REV,
        ])
        self._logger.debug("cpu load results: %r", load)
        physindexes = [row[PHYSICAL_INDEX] for row in itervalues(load)
                       if row[PHYSICAL_INDEX]]
        names = yield self._get_cpu_names(physindexes)

        result = {}
        for index, row in iteritems(load):
            name = names.get(row[PHYSICAL_INDEX], str(index[-1]))
            result[name] = [(5, row[TOTAL_5_MIN_REV]),
                            (1, row[TOTAL_1_MIN_REV])]
        defer.returnValue(result)

    @defer.inlineCallbacks
    def _get_cpu_names(self, indexes):
        if not indexes:
            defer.returnValue({})
        self._logger.debug("getting cpu names from ENTITY-MIB")
        base_oid = EntityMib.nodes['entPhysicalName'].oid
        oids = [str(base_oid + (index,)) for index in indexes]
        names = yield self.agent_proxy.get(oids)
        self._logger.debug("cpu name result: %r", names)
        names = {OID(oid)[-1]: value for oid, value in names.items() if value}
        defer.returnValue(names)

    def get_cpu_utilization(self):
        return defer.succeed(None)
