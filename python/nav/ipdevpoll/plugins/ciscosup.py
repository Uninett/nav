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
"""Assigns Supervisor software revision to chassis device on Cisco devices"""
import re

from nav.ipdevpoll import Plugin, shadows

SUPERVISOR_PATTERNS = [
    re.compile(r'supervisor', re.I),
    re.compile(r'\bSup\b'),
    re.compile(r'WS-SUP'),
    ]

class CiscoSup(Plugin):
    """Assigns Cisco Supervisor software revision to chassis"""
    @classmethod
    def can_handle(cls, netbox):
        """Handles Cisco devices and any device whose type hasn't been found"""
        daddy_says_ok = super(CiscoSup, cls).can_handle(netbox)
        return (daddy_says_ok and
                (netbox.type is None or
                 netbox.type.vendor.id.lower() == 'cisco'))

    def handle(self):
        netbox = self.containers.factory(None, shadows.Netbox)
        chassis = netbox.device
        if not chassis or chassis.software_version:
            return

        supervisor = self._find_supervisor()
        if supervisor and supervisor.device:
            chassis.software_version = supervisor.device.software_version
            self._logger.debug(
                "%s chassis software version set from supervisor: %s",
                netbox.sysname, chassis.software_version)

    def _find_supervisor(self):
        if shadows.Module not in self.containers:
            return
        modules = self.containers[shadows.Module].values()
        return find_supervisor(modules)

def find_supervisor(modules):
    """Finds and returns the supervisor module from a list of modules.

    Returns None if a supervisor module wasn't found.

    """
    for pattern in SUPERVISOR_PATTERNS:
        for module in modules:
            if pattern.search(module.description):
                return module
