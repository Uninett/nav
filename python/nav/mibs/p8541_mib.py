#
# Copyright (C) 2014 UNINETT
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
"""A class for getting temperature sensors/channels from a Comet P8541.

Comet's MIBs are highly disorganized and illogical, so any other model will
need a separate implementation, or a workaround to make a more generic
implementation for multiple MIBs must be implemented.

"""

from twisted.internet import defer
from nav.mibs.mibretriever import MibRetriever

DEGREES_CELSIUS = "\xb0C"
DEGREES_FAHRENHEIT = "\xb0F"
UNIT_MAP = {
    DEGREES_CELSIUS: "Celsius",
    DEGREES_FAHRENHEIT: "Fahrenheit",
}


class P8541Mib(MibRetriever):
    from nav.smidumps.p8541_mib import MIB as mib

    def get_module_name(self):
        """Returns the MIB module name"""
        return self.mib.get('moduleName', None)

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Returns the temperature sensor channels for this probe."""
        self._logger.warning("collecting Comet channels")
        result = []
        for channel in range(1, 5):
            o_name = "ch%dName" % channel
            o_unit = "ch%dUnit" % channel
            o_value = "ch%dIntVal" % channel
            value_oid = self.nodes[o_value].oid

            name = yield self.get_next(o_name)
            unit = yield self.get_next(o_unit)
            unit = UNIT_MAP.get(unit, unit)
            self._logger.debug("channel name/unit: %r/%r", name, unit)

            result.append(dict(
                oid=str(value_oid) + '.0',
                unit_of_measurement=unit,
                precision=1,
                scale=None,
                description=name,
                name="Channel %s" % channel,
                internal_name="channel%s" % channel,
                mib=self.get_module_name(),
            ))
        defer.returnValue(result)
