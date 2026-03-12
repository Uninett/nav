"""Tests for nav.web.ipam.util"""

import pytest
from IPy import IP

from nav.models.manage import Prefix, Vlan
from nav.web.ipam.util import get_available_subnets


class TestGetAvailableSubnets:
    def test_get_available_subnets(self, prefixes):
        available = get_available_subnets("10.0.160.0/19")
        assert available is not None
        # only 10.0.160.0/21 should be available
        assert len(available) == 1
        assert available[0] == IP("10.0.160.0/21")


###
#
# Fixtures
#
###


@pytest.fixture
def vlan(db):
    """Creates a VLAN for testing prefix availability."""
    vlan = Vlan(vlan=1337, net_type_id='lan', net_ident='cool_vlans')
    vlan.save()
    yield vlan
    # Cleanup handled by db fixture's transaction rollback


@pytest.fixture
def prefixes(vlan):
    """Creates a parent prefix with several "child" prefixes to test availability.

    The 10.0.160.0/19 scope contains four /21 subnets:
    - 10.0.160.0/21 (available)
    - 10.0.168.0/21 (used)
    - 10.0.176.0/21 (used)
    - 10.0.184.0/21 (used)
    """
    parent = Prefix(net_address='10.0.160.0/19', vlan=vlan)
    parent.save()

    child1 = Prefix(net_address='10.0.168.0/21', vlan=vlan)
    child1.save()

    child2 = Prefix(net_address='10.0.176.0/21', vlan=vlan)
    child2.save()

    child3 = Prefix(net_address='10.0.184.0/21', vlan=vlan)
    child3.save()

    yield [parent, child1, child2, child3]
    # Cleanup handled by db fixture's transaction rollback
