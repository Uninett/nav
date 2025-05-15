#
# Copyright (C) 2008-2012 Uninett AS
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
""" """

from twisted.internet import defer

from nav.mibs import reduce_index
from nav.smidumps import get_mib
from nav.mibs import mibretriever


class IfMib(mibretriever.MibRetriever):
    mib = get_mib('IF-MIB')

    def get_if_table_last_change(self):
        "Retrieves the sysUpTime value of the last time ifTable changed"
        return self.get_next('ifTableLastChange')

    @defer.inlineCallbacks
    def get_if_table(self):
        df = self.retrieve_table('ifTable')
        df.addCallback(self.translate_result)
        df.addCallback(reduce_index)
        if_table = yield df
        return if_table

    @defer.inlineCallbacks
    def get_ifnames(self):
        """Retrieves ifName and ifDescr for all interfaces.

        :returns: A dictionary like { ifindex: (ifName, ifDescr), ...}

        """
        table = yield self.retrieve_columns(['ifName', 'ifDescr']).addCallback(
            reduce_index
        )
        result = dict(
            (index, (row['ifName'], row['ifDescr'])) for index, row in table.items()
        )
        return result

    @defer.inlineCallbacks
    def get_ifaliases(self):
        """Retrieves ifAlias value for all interfaces.

        :returns: A dictionary like { ifindex: ifAlias, ... }

        """
        aliases = yield self.retrieve_column('ifAlias').addCallback(reduce_index)
        return aliases

    @defer.inlineCallbacks
    def get_ifindexes(self):
        "Retrieves a list of current ifIndexes"
        indexes = yield self.retrieve_column('ifIndex')
        return indexes.values()

    @defer.inlineCallbacks
    def get_admin_status(self):
        """Retrieves ifAdminStatus for all interfaces.

        :returns: A dictionary like { ifindex: ifAdminStatusfName, ...}

        """
        df = self.retrieve_columns(['ifAdminStatus'])
        df.addCallback(self.translate_result)
        df.addCallback(reduce_index)
        status = yield df

        result = dict((index, row['ifAdminStatus']) for index, row in status.items())
        return result

    @defer.inlineCallbacks
    def get_stack_status(self):
        """Gets the interface stacking status of the device.

        :returns: A deferred whose result is a list of (higher, lower) tuples of
                  ifindexes. Entries that don't indicate stacking are removed
                  from the result.

        """
        status = yield self.retrieve_columns(['ifStackStatus'])
        result = [
            (higher, lower)
            for higher, lower in status.keys()
            if higher > 0 and lower > 0
        ]
        return result
