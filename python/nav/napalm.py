#
# Copyright (C) 2020 Uninett AS
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
"""This module contains NAPALM connectivity interfaces for NAV"""

import weakref
from tempfile import NamedTemporaryFile
from typing import TypeVar
import logging
import napalm
from napalm.base import NetworkDriver

from nav.models import manage

DEFAULT_TIMEOUT_SECONDS = 60

Host = TypeVar("Host", str, manage.Netbox)
_logger = logging.getLogger(__name__)


def connect(host: Host, profile: manage.ManagementProfile) -> NetworkDriver:
    """Opens and returns a NAPALM connection"""
    driver = get_driver(profile)
    config = profile.configuration
    hostname = host if not isinstance(host, manage.Netbox) else host.ip
    optional_args = {
        "config_lock": True,
        "lock_disable": True,
    }
    key_file = _write_key_to_temporary_file(config, optional_args)

    try:
        device = driver(
            hostname=hostname,
            username=config.get("username"),
            password=config.get("password"),
            timeout=config.get("timeout") or DEFAULT_TIMEOUT_SECONDS,
            optional_args=optional_args,
        )
        # Let temporary file live as long as the device connection exists
        if key_file:
            weakref.finalize(device, key_file.close)
        device.open()
        return device
    except Exception:  # noqa: BLE001
        # but remove it immediately if device was never created
        if key_file:
            key_file.close()
        raise


def _write_key_to_temporary_file(config: dict, optional_args: dict):
    if config.get("private_key"):
        key_file = NamedTemporaryFile(mode="w+")
        key_file.write(config["private_key"])
        key_file.flush()
        optional_args["key_file"] = key_file.name
        return key_file


def get_driver(
    profile: manage.ManagementProfile,
) -> type[napalm.base.base.NetworkDriver]:
    """Returns a NAPALM NetworkDriver based on a management profile config"""
    if profile.protocol != profile.PROTOCOL_NAPALM:
        raise NapalmError("Management profile is not a NAPALM profile")
    driver = profile.configuration.get("driver")
    if not driver:
        raise NapalmError("Management profile has no configured driver")
    return napalm.get_network_driver(driver)


class NapalmError(Exception):
    """Raised when there is a problem with NAPALM management profiles"""
