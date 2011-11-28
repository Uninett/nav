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

from nav.ipdevpoll import Plugin, shadows

class CiscoSup(Plugin):
    @classmethod
    def can_handle(cls, netbox):
        """Handles Cisco devices and any device whose type hasn't been found"""
        return netbox.type is None or netbox.type.vendor.id.lower() == 'cisco'

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

        for module in modules:
            if 'supervisor' in module.description.lower():
                return module

        for module in modules:
            if 'WS-SUP' in module.description:
                return module
