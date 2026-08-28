"""Tests for per-attribute PortAdmin authorization, against real database objects"""

import pytest

from nav.models.manage import NetboxGroup
from nav.models.profiles import AccountGroup, PrivilegeType
from nav.portadmin.privileges import PortadminPermissions, PortadminPrivilege


def _grant(account_group, privilege, target):
    """Grants a PortAdmin privilege to an account group, scoped to a target"""
    return account_group.privileges.create(
        type=PrivilegeType.objects.get(name=privilege), target=target
    )


@pytest.fixture()
def account_group(db, non_admin_account):
    """An account group holding the account whose privileges are under test"""
    group = AccountGroup.objects.create(name="portadmin privilege test group")
    non_admin_account.groups.add(group)
    return group


@pytest.fixture()
def sdn_group(db):
    group = NetboxGroup.objects.create(id="SDN", description="SDN switches")
    return group


@pytest.fixture()
def legacy_group(db):
    group = NetboxGroup.objects.create(id="LEGACY", description="Legacy switches")
    return group


@pytest.fixture()
def sdn_netbox(localhost, sdn_group):
    localhost.groups.add(sdn_group)
    return localhost


@pytest.fixture()
def legacy_netbox(localhost, legacy_group):
    localhost.groups.add(legacy_group)
    return localhost


class TestPortadminPermissions:
    def test_when_user_is_admin_it_should_allow_everything(
        self, admin_account, sdn_netbox
    ):
        permissions = PortadminPermissions(admin_account, sdn_netbox)
        for privilege in PortadminPrivilege:
            assert permissions.can(privilege)

    def test_when_user_has_no_privileges_it_should_allow_nothing(
        self, non_admin_account, sdn_netbox
    ):
        permissions = PortadminPermissions(non_admin_account, sdn_netbox)
        for privilege in PortadminPrivilege:
            assert not permissions.can(privilege)

    def test_when_a_privilege_is_granted_then_can_edit_something_should_be_true(
        self, non_admin_account, account_group, sdn_netbox
    ):
        _grant(account_group, PortadminPrivilege.DESCRIPTION, "SDN")
        permissions = PortadminPermissions(non_admin_account, sdn_netbox)
        assert permissions.can_edit_something

    def test_when_no_privileges_are_granted_then_can_edit_something_should_be_false(
        self, non_admin_account, sdn_netbox
    ):
        permissions = PortadminPermissions(non_admin_account, sdn_netbox)
        assert not permissions.can_edit_something

    def test_when_netbox_is_outside_the_privilege_target_it_should_not_be_allowed(
        self, non_admin_account, account_group, sdn_netbox
    ):
        _grant(account_group, PortadminPrivilege.VLAN, "^LEGACY$")
        permissions = PortadminPermissions(non_admin_account, sdn_netbox)
        assert not permissions.vlan

    def test_when_target_names_a_group_it_should_match_that_group(
        self, non_admin_account, legacy_netbox, account_group
    ):
        _grant(account_group, PortadminPrivilege.VLAN, "^LEGACY$")
        permissions = PortadminPermissions(non_admin_account, legacy_netbox)
        assert permissions.vlan

    def test_when_target_matches_everything_it_should_match_any_group(
        self, non_admin_account, sdn_netbox, account_group
    ):
        _grant(account_group, PortadminPrivilege.VLAN, ".*")
        permissions = PortadminPermissions(non_admin_account, sdn_netbox)
        assert permissions.vlan

    def test_when_netbox_is_in_no_group_it_should_not_match_any_target(
        self, non_admin_account, localhost, account_group
    ):
        """A target only matches group names, so a netbox without any matches none"""
        _grant(account_group, PortadminPrivilege.VLAN, ".*")
        permissions = PortadminPermissions(non_admin_account, localhost)
        assert not permissions.vlan

    def test_when_target_is_unanchored_it_should_match_substrings(
        self, non_admin_account, localhost, account_group
    ):
        """Anchor a target with ^ and $ to match a group name exactly"""
        edge = NetboxGroup.objects.create(id="SDN-EDGE", description="Edge switches")
        localhost.groups.add(edge)
        _grant(account_group, PortadminPrivilege.VLAN, "SDN")
        permissions = PortadminPermissions(non_admin_account, localhost)
        assert permissions.vlan

    def test_when_target_is_an_invalid_regexp_it_should_not_match(
        self, non_admin_account, sdn_netbox, account_group
    ):
        """A malformed target must be denied rather than raise"""
        _grant(account_group, PortadminPrivilege.VLAN, "*")
        permissions = PortadminPermissions(non_admin_account, sdn_netbox)
        assert not permissions.vlan

    def test_when_privilege_name_is_unknown_it_should_raise_error(
        self, non_admin_account, sdn_netbox
    ):
        permissions = PortadminPermissions(non_admin_account, sdn_netbox)

        with pytest.raises(ValueError):
            permissions.can("some_other_privilege")

    def test_when_netbox_is_in_several_groups_it_should_match_any_of_them(
        self, non_admin_account, localhost, sdn_group, legacy_group, account_group
    ):
        localhost.groups.add(sdn_group, legacy_group)
        _grant(account_group, PortadminPrivilege.VLAN, "LEGACY")
        permissions = PortadminPermissions(non_admin_account, localhost)
        assert permissions.vlan

    @pytest.mark.parametrize(
        "privilege,accessor",
        [
            (PortadminPrivilege.VLAN, "vlan"),
            (PortadminPrivilege.DESCRIPTION, "description"),
            (PortadminPrivilege.ADMIN_STATUS, "admin_status"),
            (PortadminPrivilege.POE, "poe"),
            (PortadminPrivilege.VOICE_VLAN, "voice_vlan"),
            (PortadminPrivilege.TRUNK, "trunk"),
        ],
    )
    def test_when_a_privilege_is_granted_its_accessor_should_be_true(
        self, non_admin_account, sdn_netbox, account_group, privilege, accessor
    ):
        """Each privilege must map to the accessor that reports it"""
        _grant(account_group, privilege, ".*")

        permissions = PortadminPermissions(non_admin_account, sdn_netbox)

        assert getattr(permissions, accessor)
        assert permissions.allowed == frozenset([privilege])
