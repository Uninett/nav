# -*- coding: utf-8 -*-
#
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
"""
A class that collects the oids for fan- and psu-sensors,- and their
corresponding fan- and psu-statuses.

The class is specific for CISCO netboxes and use the
CISCO-ENTITY-FRU-CONTROL-MIB to collect sensor-oids and read statuses.
"""

from twisted.internet import defer

from nav.smidumps import get_mib
from nav.mibs import mibretriever, reduce_index


class CiscoEntityFruControlMib(mibretriever.MibRetriever):
    """
    A class that collects the oids for fan- and psu-sensors,- and their
    corresponding fan and psu-status.
    """
    mib = get_mib('CISCO-ENTITY-FRU-CONTROL-MIB')

    def __init__(self, agent_proxy):
        """Good old constructor..."""
        super(CiscoEntityFruControlMib, self).__init__(agent_proxy)
        self.fan_status_table = None
        self.psu_status_table = None

    @defer.inlineCallbacks
    def _get_named_table(self, table_name):
        """Retrive table with the given name. """
        df = self.retrieve_table(table_name)
        df.addCallback(self.translate_result)
        named_table = yield df.addCallback(reduce_index)
        defer.returnValue(named_table)

    @defer.inlineCallbacks
    def _get_fantray_status_table(self):
        """Retrieve the whole table of fan-sensors."""
        table = yield self._get_named_table('cefcFanTrayStatusTable')
        defer.returnValue(table)

    @defer.inlineCallbacks
    def _get_power_status_table(self):
        """Retrieve the whole table of PSU-sensors."""
        table = yield self._get_named_table('cefcFRUPowerStatusTable')
        defer.returnValue(table)

    def _get_fan_status_value(self, oper_status):
        status = 'u'
        self._logger.debug('_get_fan_status_value: %s' % oper_status)
        if oper_status == 'up':
            status = 'y'
        elif oper_status == 'down':
            status = 'n'
        elif oper_status == 'warning':
            status = 'w'
        return status

    def _get_psu_status_value(self, oper_status):
        status = 'u'
        self._logger.debug('_get_psu_status_value: %s' % oper_status)
        if oper_status == 'on':
            status = 'y'
        elif oper_status == 'onButFanFail':
            status = 'w'
        elif oper_status == 'offAdmin':
            status = 'u'
        if oper_status in ('offEnvOther', 'offDenied', 'offEnvPower',
                           'offEnvTemp', 'offEnvFan', 'failed', 'offCooling',
                           'offConnectorRating', 'onButInlinePowerFail'):
            status = 'n'
        return status

    @defer.inlineCallbacks
    def is_fan_up(self, idx):
        """Return operation-status for fan with the given index."""
        # Return status undecided if not able to extract status.
        is_up = None
        if not self.fan_status_table:
            self.fan_status_table = yield self._get_fantray_status_table()
        self._logger.debug('fan_status_table: %s' % self.fan_status_table)
        fan_status_row = self.fan_status_table.get(idx, None)
        if fan_status_row:
            fan_status = fan_status_row.get('cefcFanTrayOperStatus', None)
            if fan_status:
                is_up = self._get_fan_status_value(fan_status)
        defer.returnValue(is_up)

    @defer.inlineCallbacks
    def is_psu_up(self, idx):
        """Return operation-status for PSU with the given index."""
        # Return status undecided if not able to extract status.
        is_up = None
        if not self.psu_status_table:
            self.psu_status_table = yield self._get_power_status_table()
        self._logger.debug('psu_status_table: %s' % self.psu_status_table)
        psu_status_row = self.psu_status_table.get(idx, None)
        if psu_status_row:
            psu_status = psu_status_row.get('cefcFRUPowerOperStatus', None)
            if psu_status:
                is_up = self._get_psu_status_value(psu_status)
        defer.returnValue(is_up)

    @defer.inlineCallbacks
    def get_fan_status_table(self):
        """Retrieve the whole table of fan-sensors and cache the result."""
        if not self.fan_status_table:
            self.fan_status_table = yield self._get_fantray_status_table()
        defer.returnValue(self.fan_status_table)

    @defer.inlineCallbacks
    def get_psu_status_table(self):
        """Retrieve the whole table of PSU-sensors and cache the result."""
        if not self.psu_status_table:
            self.psu_status_table = yield self._get_power_status_table()
        defer.returnValue(self.psu_status_table)

    def get_oid_for_fan_status(self, idx):
        """Get the OID for the fan sensor with the given index."""
        oid = None
        oper_status_oid = self.nodes.get('cefcFanTrayOperStatus', None)
        if oper_status_oid:
            oid = '%s.%d' % (str(oper_status_oid.oid), idx)
        return oid

    def get_oid_for_psu_status(self, idx):
        """Get the OID for the PSU sensor with the given index."""
        oid = None
        oper_status_oid = self.nodes.get('cefcFRUPowerOperStatus', None)
        if oper_status_oid:
            oid = '%s.%d' % (str(oper_status_oid.oid), idx)
        return oid
