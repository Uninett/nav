#
# Copyright (C) 2023 Sikt
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
"""Helper functions to build SNMP sessions from NAV ManagementProfile instances"""

from functools import partial
from typing import Callable

from nav.models.manage import ManagementProfile
from nav.Snmp import Snmp


def get_snmp_session_for_profile(profile: ManagementProfile) -> Callable:
    """Returns a nav.Snmp.Snmp constructor partially pre-configured with SNMP options
    from an SNMP management profile.

    Example usage:
    >>> netbox = Netbox.objects.get(id=1)
    >>> snmp = get_snmp_session_for_profile(
    ...   netbox.get_preferred_snmp_management_profile())
    >>> session = snmp(netbox.ip)
    >>> session.get()
    b'Linux 16e2ac5c6456 6.1.60 #1-NixOS SMP PREEMPT_DYNAMIC Wed Oct 25 10:03:17 UTC 2023 x86_64'
    >>>
    """  # noqa: E501
    if not profile.is_snmp:
        raise ValueError("Cannot create SNMP session from non-SNMP management profile")

    if profile.snmp_version < 3:
        kwargs = {
            "version": profile.configuration.get("version"),
            "community": profile.configuration.get("community"),
        }
    else:
        kwargs = {
            opt: profile.configuration.get(opt) or None
            for opt in (
                "sec_level",
                "auth_protocol",
                "sec_name",
                "auth_password",
                "priv_protocol",
                "priv_password",
            )
        }
        kwargs["version"] = 3

    return partial(Snmp, **kwargs)
