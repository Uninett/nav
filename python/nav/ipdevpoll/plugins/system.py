#
# Copyright (C) 2011 UNINETT AS
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
"""Collects system information from SNMPv2-MIB"""

import re

from twisted.internet.defer import inlineCallbacks

from nav.ipdevpoll import Plugin, shadows
from nav.mibs.snmpv2_mib import Snmpv2Mib

PATTERNS = [
    re.compile(r"Version (?P<version>[^,]+)"),
    re.compile(r"V(?P<version>[0-9]+[0-9A-Za-z.]*)"),
    re.compile(r"SW:(?P<version>v?[0-9]+[0-9A-Za-z.]*)"),
    re.compile(r" (?P<version>[0-9]+\.[0-9A-Za-z.]+)"),
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
        if not netbox.device:
            device = self.containers.factory(None, shadows.Device)
            netbox.device = device
        if not device.software_version:
            device.software_version = version


def parse_version(sysdescr):
    """Parses sysDescr according to known patterns and returns a software
    version number.

    """
    for pattern in PATTERNS:
        match = pattern.search(sysdescr)
        if match:
            return match.group('version')
