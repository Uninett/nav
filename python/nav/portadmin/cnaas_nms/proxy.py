#
# Copyright (C) 2021 UNINETT
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
from nav.models import manage
from nav.portadmin.config import CONFIG
from nav.portadmin.cnaas_nms.lowlevel import get_api
from nav.portadmin.handlers import (
    ManagementHandler,
    DeviceNotConfigurableError,
    ProtocolError,
)


class CNaaSNMSMixIn(ManagementHandler):
    """MixIn to override all write-operations from
    nav.portadmin.handlers.ManagementHandler and instead direct them through a CNaaS
    NMS instance's REST API.

    """

    def __init__(self, netbox: manage.Netbox, **kwargs):
        super().__init__(netbox, **kwargs)
        config = CONFIG.get_cnaas_nms_config()
        self._api = get_api(config.url, config.token)

    def set_interface_description(self, interface: manage.Interface, description: str):
        data = {"description": interface.ifalias}
        payload = {"interfaces": {interface.ifdescr: data}}
        self._api.interfaces.configure(self.netbox.sysname, body=payload)

    def set_interface_down(self, interface: manage.Interface):
        self._set_interface_enabled(interface, enabled=False)

    def set_interface_up(self, interface: manage.Interface):
        self._set_interface_enabled(interface, enabled=True)

    def _set_interface_enabled(self, interface: manage.Interface, enabled=True):
        data = {"enabled": enabled}
        payload = {"interfaces": {interface.ifdescr: data}}
        self._api.interfaces.configure(self.netbox.sysname, body=payload)

    def commit_configuration(self):
        payload = {"hostname": self.netbox.sysname, "dry_run": False, "auto_push": True}
        self._api.device_sync.syncto(body=payload)
        # TODO: Get a job number from the syncto call
        # TODO: Poll the job API for "status": "FINISHED"

    def raise_if_not_configurable(self):
        response = self._api.devices.retrieve(self.netbox.sysname)
        payload = response.body
        if response.status_code == 200 and payload.get("status") == "success":
            if len(payload.get("devices", []) < 0):
                raise CNaaSNMSApiError("No devices match this name in CNaaS NMS")
            device = payload["devices"][0]
            if not (
                device.get("state") == "MANAGED"
                and device.get("device_type") == "ACCESS"
                and device.get("synchronized")
            ):
                raise DeviceNotConfigurableError(
                    "CNaaS NMS will not permit configuration of this device"
                )
        else:
            raise CNaaSNMSApiError("Cannot verify device status in CNaaS NMS")


class CNaaSNMSApiError(ProtocolError):
    """An exception raised whenever there is a problem with the responses from the
    CNaaS NMS API
    """
