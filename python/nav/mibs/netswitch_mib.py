#
# Copyright (C) 2013 Uninett AS
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
from twisted.internet import defer
from nav.smidumps import get_mib
from nav.mibs import mibretriever

LOCAL_SLOT = 'hpLocalMemSlotIndex'
LOCAL_FREE = 'hpLocalMemFreeBytes'
LOCAL_USED = 'hpLocalMemAllocBytes'

GLOBAL_SLOT = 'hpGlobalMemSlotIndex'
GLOBAL_FREE = 'hpGlobalMemFreeBytes'
GLOBAL_USED = 'hpGlobalMemAllocBytes'

MEMORY_OIDS = {
    'local': [LOCAL_SLOT, LOCAL_FREE, LOCAL_USED],
    'global': [GLOBAL_SLOT, GLOBAL_FREE, GLOBAL_USED],
}


class NetswitchMib(mibretriever.MibRetriever):
    mib = get_mib('NETSWITCH-MIB')

    @defer.inlineCallbacks
    def get_memory_usage(self):
        """Retrieves memory usage stats from a HP device.

        :returns: A deferred whose result is a dict
                  {slot_type: (used_bytes, free_bytes)}

        """
        result = dict()
        for kind, (slot_oid, free_oid, used_oid) in MEMORY_OIDS.items():
            slots = yield self.retrieve_columns([slot_oid, free_oid, used_oid])
            for row in slots.values():
                result[kind + str(row[slot_oid])] = (row[used_oid], row[free_oid])
        return result
