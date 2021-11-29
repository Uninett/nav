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
import time
from typing import Sequence
import logging

from nav.models import manage
from nav.portadmin.config import CONFIG
from nav.portadmin.cnaas_nms.lowlevel import get_api, ClientError
from nav.portadmin.handlers import (
    ManagementHandler,
    DeviceNotConfigurableError,
    ProtocolError,
)

_logger = logging.getLogger(__name__)


class CNaaSNMSMixIn(ManagementHandler):
    """MixIn to override all write-operations from
    nav.portadmin.handlers.ManagementHandler and instead direct them through a CNaaS
    NMS instance's REST API.

    """

    def __init__(self, netbox: manage.Netbox, **kwargs):
        super().__init__(netbox, **kwargs)
        config = CONFIG.get_cnaas_nms_config()
        self._api = get_api(config.url, config.token, config.ssl_verify)
        self._device = None

    def set_interface_description(self, interface: manage.Interface, description: str):
        data = {"description": interface.ifalias}
        payload = {"interfaces": {interface.ifdescr: data}}
        self._api.interfaces.configure(self.device_name, body=payload)

    def set_interface_down(self, interface: manage.Interface):
        self._set_interface_enabled(interface, enabled=False)

    def set_interface_up(self, interface: manage.Interface):
        self._set_interface_enabled(interface, enabled=True)

    def _set_interface_enabled(self, interface: manage.Interface, enabled=True):
        data = {"enabled": enabled}
        payload = {"interfaces": {interface.ifdescr: data}}
        self._api.interfaces.configure(self.device_name, body=payload)

    def _bounce_interfaces(
        self,
        interfaces: Sequence[manage.Interface],
        wait: float = 5.0,
        commit: bool = False,
    ):
        """Offloads the entire bounce operation to CNaaS NMS. CNaaS NMS doesn't need
        or care about the wait and commit arguments, so these are flatly ignored.
        """
        payload = {"bounce_interfaces": [ifc.ifdescr for ifc in interfaces]}
        self._api.interface_status.update(self.device_name, body=payload)

    def commit_configuration(self):
        job_id = self._device_syncto()
        job = self._poll_job_until_finished(job_id)
        self._raise_on_job_failure(job)

    def _device_syncto(self) -> int:
        """Runs the CNaaS-NMS device_syncto operation and returns its job number"""
        payload = {"hostname": self.device_name, "dry_run": False, "auto_push": True}
        response = self._api.device_sync.syncto(body=payload)
        assert response.body.get("status") == "success"
        job_id = response.body.get("job_id")
        message = response.body.get("data")
        _logger.debug(
            "%s device_syncto response (job_id: %s): %s",
            self.device_name,
            job_id,
            message,
        )
        return job_id

    def _poll_job_until_finished(self, job_id: int, retry_delay: float = 1.0) -> dict:
        job = None
        status = "SCHEDULED"
        while status.upper() in ("SCHEDULED", "RUNNING"):
            time.sleep(retry_delay)
            job = self._get_job(job_id)
            status = job.get("status")
            _logger.debug(
                "%s polled job status for job_id=%s: %s",
                self.device_name,
                job_id,
                status,
            )
        return job

    def _get_job(self, job_id: int) -> dict:
        response = self._api.jobs.retrieve(job_id)
        return response.body.get("data").get("jobs")[0]

    def _raise_on_job_failure(self, job: dict):
        if job.get("status") != "FINISHED":
            message = job.get("result", {}).get("message")
            if not message:
                message = "Unknown error from CNaaS-NMS job %s, please see logs".format(
                    job.get("id")
                )
                _logger.error("%s device_syncto job failed: %r", job)
            raise ProtocolError(message)

    def raise_if_not_configurable(self):
        """Raises an exception if this device cannot be configured by CNaaS-NMS for
        some reason.
        """
        try:
            device = self._get_device_record()
            self.raise_on_unmatched_criteria(device)
        except CNaaSNMSApiError as error:
            raise DeviceNotConfigurableError(str(error)) from error
        except ClientError as error:
            raise DeviceNotConfigurableError(
                "Unexpected error talking to the CNaaS-NMS backend: " + str(error)
            ) from error

    def raise_on_unmatched_criteria(self, device_record):
        """Raises an exception if the device's CNaaS-NMS attributes do not match the
        preset criteria for being managed via the API.
        """
        state = device_record.get("state")
        device_type = device_record.get("device_type")
        synchronized = device_record.get("synchronized")

        if state != "MANAGED":
            raise DeviceNotConfigurableError(
                "CNaaS-NMS does not list this device as managed ({})".format(state)
            )
        if device_type != "ACCESS":
            raise DeviceNotConfigurableError(
                "Cannot use CNaaS-NMS to configure {} type devices".format(device_type)
            )
        if not synchronized:
            raise DeviceNotConfigurableError(
                "Device configuration is not synchronized with CNaaS-NMS, cannot make "
                "changes at the moment. Please try againt later."
            )

    @property
    def device_name(self) -> str:
        """This returns the name used for this device in CNaaS NMS. It does not
        necessarily correspond to the sysname NAV got from DNS, but is necessary to
        construct most API operations against the device.
        """
        if not self._device:
            self._device = self._get_device_record()
        return self._device.get("hostname")

    def _get_device_record(self):
        response = self._api.devices.retrieve(self.netbox.ip)
        payload = response.body
        if response.status_code == 200 and payload.get("status") == "success":
            data = payload.get("data", {})
            if len(data.get("devices", [])) < 0:
                raise CNaaSNMSApiError(
                    "No devices matched {} in CNaaS-NMS".format(self.netbox.ip)
                )
            device = data["devices"][0]
            return device
        else:
            raise CNaaSNMSApiError(
                "Unknown failure when talking to CNaaS-NMS (code={}, status={})".format(
                    response.status_code, payload.get("status")
                )
            )


class CNaaSNMSApiError(ProtocolError):
    """An exception raised whenever there is a problem with the responses from the
    CNaaS NMS API
    """
