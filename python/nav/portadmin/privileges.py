#
# Copyright (C) 2026 Sikt
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
"""Defines granular privileges for PortAdmin."""

from enum import StrEnum

from nav.models.manage import Netbox
from nav.models.profiles import Account
from nav.portadmin.config import CONFIG


class PortadminPrivilege(StrEnum):
    """The PortAdmin privilege type names

    These correspond to rows in the `privilege` database table, and to the
    individually editable attributes exposed by PortAdmin. The members compare equal
    to their string values, so they can be used directly in database queries.
    """

    VLAN = "portadmin_vlan"
    DESCRIPTION = "portadmin_description"
    ADMIN_STATUS = "portadmin_admin_status"
    POE = "portadmin_poe"
    VOICE_VLAN = "portadmin_voice_vlan"
    TRUNK = "portadmin_trunk"


class PortadminPermissions:
    """The set of PortAdmin attributes an account may edit on a given netbox.

    Privileges are granted per user group.
    A netbox that belongs to no device group matches no target, and no privilege
    applies to it.

    Enforcement is controlled by the ``require_privileges`` option in the
    ``[authorization]`` section of :file:`portadmin.conf`, and is off by default.
    """

    def __init__(self, account: Account, netbox: Netbox):
        self.account = account
        self.netbox = netbox
        self._is_admin = account.is_admin()
        self._enforced = CONFIG.is_privilege_authorization_enabled()
        self._allowed = (
            set(PortadminPrivilege)
            if self._is_admin or not self._enforced
            else self._resolve_allowed_privileges()
        )

    def _resolve_allowed_privileges(self) -> set[str]:
        """Finds the privileges granted to this account that apply to this netbox"""
        privileges = self.account.get_privileges().filter(
            type__name__in=list(PortadminPrivilege),
            target__in=self.netbox.groups.values_list("id", flat=True),
        )
        return set(privileges.values_list("type__name", flat=True))

    def can(self, privilege: str) -> bool:
        """Returns True if the account may change the given attribute

        :raises ValueError: If the privilege is not a PortAdmin privilege.
        """
        return PortadminPrivilege(privilege) in self._allowed

    @property
    def can_edit_something(self) -> bool:
        """Returns True if the account may change at least one attribute"""
        return bool(self._allowed)

    @property
    def allowed(self) -> frozenset[str]:
        """Returns the set of privilege names granted on this netbox"""
        return frozenset(self._allowed)

    # Convenience accessors, primarily for use from Django templates

    @property
    def vlan(self) -> bool:
        """Returns True if the account may change the VLAN"""
        return self.can(PortadminPrivilege.VLAN)

    @property
    def description(self) -> bool:
        """Returns True if the account may change the port description"""
        return self.can(PortadminPrivilege.DESCRIPTION)

    @property
    def admin_status(self) -> bool:
        """Returns True if the account may enable/disable the interface"""
        return self.can(PortadminPrivilege.ADMIN_STATUS)

    @property
    def poe(self) -> bool:
        """Returns True if the account may change the PoE state"""
        return self.can(PortadminPrivilege.POE)

    @property
    def voice_vlan(self) -> bool:
        """Returns True if the account may change the voice VLAN"""
        return self.can(PortadminPrivilege.VOICE_VLAN)

    @property
    def trunk(self) -> bool:
        """Returns True if the account may edit trunks"""
        return self.can(PortadminPrivilege.TRUNK)
