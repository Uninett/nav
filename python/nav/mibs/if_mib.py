#
# Copyright (C) 2008-2012 UNINETT AS
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


class IfMib(mibretriever.MibRetriever):
    from nav.smidumps.if_mib import MIB as mib

    @defer.inlineCallbacks
    def get_if_table(self):
        df = self.retrieve_table('ifTable')
        df.addCallback(self.translate_result)
        df.addCallback(reduce_index)
        if_table = yield df
        defer.returnValue(if_table)

    @defer.inlineCallbacks
    def get_ifnames(self):
        """Retrieves ifName and ifDescr for all interfaces.

        :returns: A dictionary like { ifindex: (ifName, ifDescr), ...}

        """
        table = yield self.retrieve_columns(
            ['ifName', 'ifDescr']).addCallback(reduce_index)
        result = dict((index, (row['ifName'], row['ifDescr']))
                      for index, row in table.items())
        defer.returnValue(result)

    @defer.inlineCallbacks
    def get_ifindexes(self):
        "Retrieves a list of current ifIndexes"
        indexes = yield self.retrieve_column('ifIndex')
        defer.returnValue(indexes.values())

    @defer.inlineCallbacks
    def get_admin_status(self):
        """Retrieves ifAdminStatus for all interfaces.

        :returns: A dictionary like { ifindex: ifAdminStatusfName, ...}

        """
        df = self.retrieve_columns(['ifAdminStatus'])
        df.addCallback(self.translate_result)
        df.addCallback(reduce_index)
        status = yield df

        result = dict((index, row['ifAdminStatus'])
                      for index, row in status.items())
        defer.returnValue(result)
