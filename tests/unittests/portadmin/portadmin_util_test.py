"""Testing"""
import unittest
from mock import Mock
from nav.web.portadmin.utils import (find_allowed_vlans_for_user,
                                     find_vlans_in_org)
from nav.portadmin.snmputils import FantasyVlan


class TestPortAdminUtil(unittest.TestCase):
    """Test PortAdmin util functions"""

    # pylint: disable=C0103
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

        self.org1.vlan_set.all.return_value = [self.vlan1]
        self.org1.organization_set.all.return_value = [self.org2]

        self.org2.vlan_set.all.return_value = [self.vlan2]
        self.org2.organization_set.all.return_value = [self.org3]

        self.org3.vlan_set.all.return_value = [self.vlan3]
        self.org3.organization_set.all.return_value = []

    def test_find_vlans_in_org_no_children(self):
        """Should return all vlans in this org"""
        self.assertEqual(find_vlans_in_org(self.org3),
                         [FantasyVlan(self.vlan3.vlan)])

    def test_find_vlans_in_org_one_child(self):
        """Should return all vlans in this org and child org"""
        self.assertEqual(sorted(find_vlans_in_org(self.org2)),
                         sorted([FantasyVlan(self.vlan3.vlan),
                                 FantasyVlan(self.vlan2.vlan)]))

    def test_find_vlans_in_org_two_children(self):
        """Should return all vlans in this org and all children orgs"""
        self.assertEqual(sorted(find_vlans_in_org(self.org1)),
                         sorted([FantasyVlan(self.vlan3.vlan),
                                 FantasyVlan(self.vlan2.vlan),
                                 FantasyVlan(self.vlan1.vlan)]))

    def test_find_vlans_in_org_no_duplicates(self):
        """Should filter duplicates"""
        self.org3.vlan_set.all.return_value = [self.vlan3, self.vlan2]
        self.assertEqual(sorted(find_vlans_in_org(self.org1)),
                         sorted([FantasyVlan(self.vlan3.vlan),
                                 FantasyVlan(self.vlan2.vlan),
                                 FantasyVlan(self.vlan1.vlan)]))

    def test_find_vlans_in_org_filter_nonevalues(self):
        """Should filter vlans with no vlan value"""
        self.vlan1.vlan = None
        self.assertEqual(sorted(find_vlans_in_org(self.org1)),
                         sorted([FantasyVlan(self.vlan3.vlan),
                                 FantasyVlan(self.vlan2.vlan)]))

    def test_find_allowed_vlans_for_user(self):
        """Should return all vlans for this users org and child orgs"""

        account = Mock()
        account.organizations.all.return_value = [self.org1]

        self.assertEqual(sorted(find_allowed_vlans_for_user(account)),
                         sorted([FantasyVlan(self.vlan1.vlan),
                                 FantasyVlan(self.vlan2.vlan),
                                 FantasyVlan(self.vlan3.vlan)]))
