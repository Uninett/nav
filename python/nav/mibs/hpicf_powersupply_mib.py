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
""" Implements a MibRetriever for the POWERSUPPLY-MIB, as well as helper
classes.

POWERSUPPLY-MIB is a mib that can be downloaded from HP's support pages.
"""

from twisted.internet import defer

from nav.mibs import reduce_index
from nav.mibs import mibretriever


class HpIcfPowerSupplyMib(mibretriever.MibRetriever):
    """ A class for collecting powersupply states from HP netboxes."""
    from nav.smidumps.hpicf_powersupply_mib import MIB as mib

    def __init__(self, agent_proxy):
        """ Constructor, anything more to say...?"""
        super(HpIcfPowerSupplyMib, self).__init__(agent_proxy)
        self.psu_status_table = None

    @defer.inlineCallbacks
    def _get_psu_status_table(self):
        """Return the powersupply-status table from this netbox."""
        df = self.retrieve_table('hpicfPsTable')
        df.addCallback(self.translate_result)
        df.addCallback(reduce_index)
        psu_table = yield df
        self._logger.debug('psu_table: %s' % psu_table)
        defer.returnValue(psu_table)

    def _get_psu_status(self, psu_status):
        """Return the current powersupply-status.  Status is returned as a
        single character.  Return-values: u = unknown, y = ok, n = failed,
        w = warning
        """
        status = 'u'
        if psu_status == 'psNotPresent' or psu_status == 'psNotPlugged':
            status = 'u'
        elif psu_status == 'psPowered':
            status = 'y'
        elif psu_status == 'psFailed' or psu_status == 'psPermFailure':
            status = 'n'
        elif psu_status == 'psMax':
            status = 'w'
        return status

    @defer.inlineCallbacks
    def is_psu_up(self, idx):
        """Return the status of the powersupply with the given index."""
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
        """Return the full OID for the powersupply with the given index."""
        oid = None
        psu_state_oid = self.nodes.get('hpicfPsState', None)
        if psu_state_oid:
            oid = '%s.%d' % (str(psu_state_oid.oid), idx)
        return oid
