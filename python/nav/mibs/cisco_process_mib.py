#
# Copyright (C) 2013 UNINETT
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

        by_physindex = dict((row[PHYSICAL_INDEX], row)
                            for row in load.values()
                            if row[PHYSICAL_INDEX])
        if by_physindex:
            result = dict()
            names = yield self._get_cpu_names(by_physindex.keys())
            for physindex, row in by_physindex.items():
                name = names.get(physindex, None)
                if name:
                    result[name] = [(5, row[TOTAL_5_MIN_REV]),
                                    (1, row[TOTAL_1_MIN_REV])]
            defer.returnValue(result)

    @defer.inlineCallbacks
    def _get_cpu_names(self, indexes):
        base_oid = EntityMib.nodes['entPhysicalName'].oid
        oids = [str(base_oid + (index,)) for index in indexes]
        names = yield self.agent_proxy.get(oids)
        names = dict((OID(oid)[-1], value) for oid, value in names.items())
        defer.returnValue(names)

    def get_cpu_utilization(self):
        return defer.succeed(None)
