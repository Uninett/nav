"""Testing"""

import unittest
from mock import Mock
from nav.web.portadmin.utils import (
    find_allowed_vlans_for_user,
    find_vlans_in_org,
    filter_vlans,
)
from nav.portadmin.vlan import FantasyVlan


class TestPortAdminUtil(unittest.TestCase):
    """Test PortAdmin util functions"""

    def setUp(self):
        """Pre-test setup"""
        self.vlan1 = Mock()
        self.vlan1.vlan = 1

        self.vlan2 = Mock()
        self.vlan2.vlan = 2

        self.vlan3 = Mock()
        self.vlan3.vlan = 3

        self.org1 = Mock()
        self.org2 = Mock()
        self.org3 = Mock()

        self.org1.vlans.all.return_value = [self.vlan1]
        self.org1.child_organizations.all.return_value = [self.org2]

        self.org2.vlans.all.return_value = [self.vlan2]
        self.org2.child_organizations.all.return_value = [self.org3]

        self.org3.vlans.all.return_value = [self.vlan3]
        self.org3.child_organizations.all.return_value = []

    def test_find_vlans_in_org_no_children(self):
        """Should return all vlans in this org"""
        self.assertEqual(find_vlans_in_org(self.org3), [FantasyVlan(self.vlan3.vlan)])

    def test_find_vlans_in_org_one_child(self):
        """Should return all vlans in this org and child org"""
        self.assertEqual(
            sorted(find_vlans_in_org(self.org2)),
            sorted([FantasyVlan(self.vlan3.vlan), FantasyVlan(self.vlan2.vlan)]),
        )

    def test_find_vlans_in_org_two_children(self):
        """Should return all vlans in this org and all children orgs"""
        self.assertEqual(
            sorted(find_vlans_in_org(self.org1)),
            sorted(
                [
                    FantasyVlan(self.vlan3.vlan),
                    FantasyVlan(self.vlan2.vlan),
                    FantasyVlan(self.vlan1.vlan),
                ]
            ),
        )

    def test_find_vlans_in_org_no_duplicates(self):
        """Should filter duplicates"""
        self.org3.vlans.all.return_value = [self.vlan3, self.vlan2]
        self.assertEqual(
            sorted(find_vlans_in_org(self.org1)),
            sorted(
                [
                    FantasyVlan(self.vlan3.vlan),
                    FantasyVlan(self.vlan2.vlan),
                    FantasyVlan(self.vlan1.vlan),
                ]
            ),
        )

    def test_find_vlans_in_org_filter_nonevalues(self):
        """Should filter vlans with no vlan value"""
        self.vlan1.vlan = None
        self.assertEqual(
            sorted(find_vlans_in_org(self.org1)),
            sorted([FantasyVlan(self.vlan3.vlan), FantasyVlan(self.vlan2.vlan)]),
        )

    def test_find_allowed_vlans_for_user(self):
        """Should return all vlans for this users org and child orgs"""

        account = Mock()
        account.organizations.all.return_value = [self.org1]

        self.assertEqual(
            sorted(find_allowed_vlans_for_user(account)),
            sorted(
                [
                    FantasyVlan(self.vlan1.vlan),
                    FantasyVlan(self.vlan2.vlan),
                    FantasyVlan(self.vlan3.vlan),
                ]
            ),
        )

    def test_filter_vlans_add(self):
        vlans_from_request = [1, 2, 3]
        old_trunked_vlans = [3]  # Vlans from querying the netbox
        allowed_vlans = range(1, 10)

        self.assertEqual(
            filter_vlans(vlans_from_request, old_trunked_vlans, allowed_vlans),
            [1, 2, 3],
        )

    def test_filter_vlans_add_deny(self):
        """Only add vlans that are in allowed vlans"""
        vlans_from_request = [1, 2, 3]
        old_trunked_vlans = [3]  # Vlans from querying the netbox
        allowed_vlans = [1]

        self.assertEqual(
            filter_vlans(vlans_from_request, old_trunked_vlans, allowed_vlans), [1, 3]
        )

    def test_filter_vlans_remove(self):
        """It should be possible to remove vlans by not including them"""
        vlans_from_request = [1, 2]
        old_trunked_vlans = [3]
        allowed_vlans = range(1, 10)

        self.assertEqual(
            filter_vlans(vlans_from_request, old_trunked_vlans, allowed_vlans), [1, 2]
        )

    def test_filter_vlans_remove_deny(self):
        """Only remove vlans that are in allowed vlans list"""
        vlans_from_request = [2]
        old_trunked_vlans = [1, 2, 3]
        allowed_vlans = range(1, 3)

        self.assertEqual(
            filter_vlans(vlans_from_request, old_trunked_vlans, allowed_vlans), [2, 3]
        )
