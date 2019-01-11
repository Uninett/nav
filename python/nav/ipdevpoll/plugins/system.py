#
# Copyright (C) 2011,2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Collects system information from SNMPv2-MIB"""

import re

from twisted.internet.defer import inlineCallbacks

from nav.models import manage
from nav.ipdevpoll import Plugin, shadows
from nav.mibs.snmpv2_mib import Snmpv2Mib

PATTERNS = [
    re.compile(r"Version (?P<version>[^,]+)"),
    re.compile(r"V(?P<version>[0-9]+[0-9A-Za-z.]*)"),
    re.compile(r"SW:(?P<version>v?[0-9]+[0-9A-Za-z.]*)"),
    re.compile(r" (?P<version>[0-9]+\.[0-9A-Za-z.]+)"),
    re.compile(r" (?P<version>[A-Z]+\.[0-9]+\.[0-9]+)"),
    ]


class System(Plugin):
    """Collects sysDescr and parses a software version from it"""

    @inlineCallbacks
    def handle(self):
        snmpv2_mib = Snmpv2Mib(self.agent)
        sysdescr = yield snmpv2_mib.get_sysDescr()
        if sysdescr:
            self._logger.debug("sysDescr: %r", sysdescr)
            version = parse_version(sysdescr)
            self._logger.debug("Parsed version: %s", version)
            if version:
                self._set_device_version(version)

    def _set_device_version(self, version):
        netbox = self.containers.factory(None, shadows.Netbox)
        chassis = shadows.NetboxEntity.get_chassis_entities(self.containers)
        if chassis and len(chassis) == 1:
            entity = chassis[0]
            self._logger.debug("found a pre-existing chassis: %s/%s (%s)",
                               entity.name, entity.source,
                               entity.device.serial if entity.device else "N/A")
            if not entity.software_revision:
                entity.software_revision = version
                self._logger.debug("set pre-existing entity software revision")
            if entity.device and not entity.device.software_version:
                entity.device.software_version = version
                self._logger.debug("set pre-existing device software revision")

        if not chassis:
            roots = shadows.NetboxEntity.get_root_entities(self.containers)
            if roots:
                self._logger.debug(
                    "device has root entities, but none are chassis. doing "
                    "nothing about the software revisions I found")
                return

            device = self.containers.factory(None, shadows.Device)
            if not device.software_version:
                self._logger.debug(
                    "didn't find a pre-existing chassis, making one")
                device.software_version = version

                entity = self.containers.factory(None, shadows.NetboxEntity)
                entity.netbox = netbox
                entity.index = 0
                entity.source = "SNMPv2-MIB"
                entity.physical_class = manage.NetboxEntity.CLASS_CHASSIS
                entity.device = device
                entity.software_revision = version


def parse_version(sysdescr):
    """Parses sysDescr according to known patterns and returns a software
    version number.

    """
    for pattern in PATTERNS:
        match = pattern.search(sysdescr)
        if match:
            return match.group('version')
