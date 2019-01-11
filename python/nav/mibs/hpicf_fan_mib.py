# encoding: utf-8
# Copyright 2008 - 2011 (C) Uninett AS
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
""" Implements a MibRetriever for the FAN-MIB, as well as helper classes.
FAN-MIB is a mib that can be downloaded from HP's support pages.
"""
from twisted.internet import defer

from nav.mibs import reduce_index
from nav.mibs import mibretriever


class HpIcfFanMib(mibretriever.MibRetriever):
    """ A class for collecting fan states from HP netboxes."""
    from nav.smidumps.hpicf_fan_mib import MIB as mib

    def __init__(self, agent_proxy):
        """Just a constructor..."""
        super(HpIcfFanMib, self).__init__(agent_proxy)
        self.fan_status_table = None

    @defer.inlineCallbacks
    def _get_fan_status_table(self):
        """Get the fan-status table from netbox."""
        df = self.retrieve_table('hpicfFanTable')
        df.addCallback(self.translate_result)
        df.addCallback(reduce_index)
        fan_table = yield df
        self._logger.debug('fan_table: %s' % fan_table)
        defer.returnValue(fan_table)

    def _get_fan_status(self, fan_status):
        """Return the status for a fan,- represented as a single character.
        Return-values: u = unknown, n = failed, y = ok, w = warning."""
        status = 'u'
        if fan_status == 'failed':
            status = 'n'
        elif fan_status == 'removed' or fan_status == 'off':
            status = 'u'
        elif (fan_status == 'underspeeed'
                or fan_status == 'overspeed'
                  or fan_status == 'maxstate'):
            status = 'w'
        elif fan_status == 'ok':
            status = 'y'
        return status

    @defer.inlineCallbacks
    def is_fan_up(self, idx):
        """Return the status of the fan with the given index."""
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
        """Return the full OID for the fan with the given index."""
        oid = None
        fan_state_oid = self.nodes.get('hpicfFanState', None)
        if fan_state_oid:
            oid = '%s.%d' % (str(fan_state_oid.oid), idx)
        return oid
