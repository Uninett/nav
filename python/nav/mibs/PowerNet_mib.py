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
""" A class for extracting sensors from APC UPSes.
"""
from twisted.internet import defer

from nav.mibs import reduce_index
from nav.mibs import mibretriever

class PowerNetMib(mibretriever.MibRetriever):
    from nav.smidumps.PowerNet_mib import MIB as mib

    def get_module_name(self):
        """Return the MIB-name."""
        return self.mib.get('moduleName', None)

    def _get_input_voltage_sensors(self):
        """ volts """
        df = self.retrieve_columns(['atsInputVoltage'])
        df.addCallback(reduce_index)
        return df

    def _get_input_frequency_sensors(self):
        """ Hz """
        df = self.retrieve_columns(['upsAdvInputFrequency'])
        df.addCallback(reduce_index)
        return df

    def _get_output_current_sensors(self):
        """ amperes """
        df = self.retrieve_columns(['upsAdvOutputCurrent'])
        df.addCallback(reduce_index)
        return df

    def _get_temp_sensors(self):
        """ celsius """
        df = self.retrieve_columns(['mUpsEnvironAmbientTemperature'])
        df.addCallback(reduce_index)
        return df

    def _get_battery_level_sensors(self):
        """ percent """
        df = self.retrieve_columns(['upsAdvBatteryCapacity'])
        df.addCallback(reduce_index)
        return df

    def _get_battery_remaining_time_sensors(self):
        """ Timeticks:  seconds = timeticks/100 """
        df = self.retrieve_columns(['upsBasicBatteryTimeOnBattery'])
        df.addCallback(reduce_index)
        return df

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """ .... """
        return []
