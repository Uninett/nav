# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
import mibretriever

class CiscoEnvMonMib(mibretriever.MibRetriever):
    from nav.smidumps.cisco_envmon_mib import MIB as mib

    def retrieve_std_columns(self):
        """ A convenient function for getting the most interesting
        columns for environment mibs. """
        return self.retrieve_columns([
                'ciscoEnvMonVoltageStatusDescr',
                'ciscoEnvMonVoltageStatusValue',
                'ciscoEnvMonVoltageThresholdLow',
                'ciscoEnvMonVoltageThresholdHigh',
                'ciscoEnvMonVoltageLastShutdown',
                'ciscoEnvMonVoltageState',
                'ciscoEnvMonTemperatureStatusIndex',
                'ciscoEnvMonTemperatureStatusDescr',
                'ciscoEnvMonTemperatureStatusValue',
                'ciscoEnvMonTemperatureThreshold',
                'ciscoEnvMonTemperatureLastShutdown',
                'ciscoEnvMonTemperatureState',
                'ciscoEnvMonFanStatusIndex',
                'ciscoEnvMonFanStatusDescr',
                'ciscoEnvMonFanState',
                'ciscoEnvMonSupplyStatusIndex',
                'ciscoEnvMonSupplyStatusDescr',
                'ciscoEnvMonSupplyState',
                'ciscoEnvMonSupplySource',
                ])
