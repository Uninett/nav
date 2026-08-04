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

import logging
import re
from enum import StrEnum

from nav.models.manage import Netbox
from nav.models.profiles import Account

_logger = logging.getLogger(__name__)


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

    Each privilege is scoped by its ``target``, a regular expression matched against
    the names of the device groups the netbox belongs to, in the same way the targets
    of ``web_access`` privileges are regular expressions. The privilege applies if the
    expression matches at least one of the groups, so `^SDN$` covers the netboxes in
    the `SDN` device group, while `.*` covers every netbox that is in a group at all.

    Since a target only ever matches group names, a netbox that belongs to no device
    group matches no target, and no privilege applies to it.

    Instances are cheap to pass around and evaluate the account's privileges only
    once, so a single instance can be reused for every interface on a netbox.
    """

    def __init__(self, account: Account, netbox: Netbox):
        self.account = account
        self.netbox = netbox
        self._is_admin = account.is_admin()
        self._allowed = (
            set(PortadminPrivilege)
            if self._is_admin
            else self._resolve_allowed_privileges()
        )

    def _resolve_allowed_privileges(self) -> set[str]:
        """Finds the privileges granted to this account that apply to this netbox"""
        group_ids = self._get_netbox_group_ids()
        privileges = self.account.get_privileges().filter(
            type__name__in=list(PortadminPrivilege)
        )
        return {
            privilege.type.name
            for privilege in privileges
            if self._target_matches_groups(privilege.target, group_ids)
        }

    def _get_netbox_group_ids(self) -> set[str]:
        """Returns the set of device group names the netbox belongs to"""
        return set(self.netbox.groups.values_list("id", flat=True))

    @staticmethod
    def _target_matches_groups(target: str, group_ids: set[str]) -> bool:
        """Decides whether a privilege target matches a set of device groups

        The target is a regular expression, matched against each device group name.
        It matches if at least one of them matches. A netbox that belongs to no
        device group therefore matches no target at all.

        :param target: The ``target`` value of a privilege.
        :param group_ids: The device group names
        """
        if not target:
            return False
        try:
            pattern = re.compile(target)
        except re.error:
            _logger.error("Invalid regexp in PortAdmin privilege target: %r", target)
            return False
        return any(pattern.search(group_id) for group_id in group_ids)

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
