import json
import pytest

from nav.models.manage import Prefix, Vlan, NetType
from nav.compatibility import force_str
from nav.web.api.v1.views import get_endpoints

ENDPOINTS = {name: force_str(url) for name, url in get_endpoints().items()}
prefix_url = ENDPOINTS['prefix']


class TestContainsAddressFilter:
    def test_prefix_is_returned_when_no_given_containing_address(self, client, prefix):
        response = client.get(prefix_url, {"contains_address": ""})
        assert response.status_code == 200
        content = json.loads(response.content.decode('utf-8'))
        prefix_ids = [prefix['id'] for prefix in content['results']]
        assert prefix.id in prefix_ids

    def test_prefix_containing_given_address_is_returned(self, client, prefix):
        response = client.get(prefix_url, {"contains_address": "10.1.1.0/24"})
        assert response.status_code == 200
        content = json.loads(response.content.decode('utf-8'))
        prefix_ids = [prefix['id'] for prefix in content['results']]
        assert prefix.id in prefix_ids

    def test_prefix_that_does_not_contain_given_address_is_not_returned(
        self, client, prefix
    ):
        response = client.get(prefix_url, {"contains_address": "20.4.111.0/24"})
        assert response.status_code == 200
        content = json.loads(response.content.decode('utf-8'))
        prefix_ids = [prefix['id'] for prefix in content['results']]
        assert prefix.id not in prefix_ids

    def test_error_is_returned_if_given_address_is_not_valid_cidr_address(
        self, client, prefix
    ):
        response = client.get(prefix_url, {"contains_address": "invalid_address"})
        assert response.status_code == 400

    def test_prefix_identical_to_given_address_is_returned(self, client, prefix):
        response = client.get(prefix_url, {"contains_address": prefix.net_address})
        assert response.status_code == 200
        content = json.loads(response.content.decode('utf-8'))
        prefix_ids = [prefix['id'] for prefix in content['results']]
        assert prefix.id in prefix_ids


class TestVlanFilter:
    def test_prefix_with_matching_vlan_id_is_returned(self, client, prefix):
        response = client.get(prefix_url, {"vlan": prefix.vlan.id})
        assert response.status_code == 200
        content = json.loads(response.content.decode('utf-8'))
        prefix_ids = [prefix['id'] for prefix in content['results']]
        assert prefix.id in prefix_ids


class TestIsNetAddressFilter:
    def test_prefix_is_returned_when_no_given_address(self, client, prefix):
        response = client.get(prefix_url, {"net_address": ""})
        assert response.status_code == 200
        content = json.loads(response.content.decode('utf-8'))
        prefix_ids = [prefix['id'] for prefix in content['results']]
        assert prefix.id in prefix_ids

    def test_prefix_with_given_address_is_returned(self, client, prefix):
        response = client.get(prefix_url, {"net_address": prefix.net_address})
        assert response.status_code == 200
        content = json.loads(response.content.decode('utf-8'))
        prefix_ids = [prefix['id'] for prefix in content['results']]
        assert prefix.id in prefix_ids

    def test_prefix_that_is_not_given_address_is_not_returned(self, client, prefix):
        response = client.get(prefix_url, {"net_address": "20.4.111.0/24"})
        assert response.status_code == 200
        content = json.loads(response.content.decode('utf-8'))
        prefix_ids = [prefix['id'] for prefix in content['results']]
        assert prefix.id not in prefix_ids

    def test_error_is_returned_if_given_address_is_not_valid_cidr_address(
        self, client, prefix
    ):
        response = client.get(prefix_url, {"net_address": "invalid_address"})
        assert response.status_code == 400


###
#
# Fixtures
#
###


@pytest.fixture()
def nettype(db):
    nettype = NetType(description="test nettype")
    nettype.save()
    yield nettype
    if nettype.pk:
        nettype.delete()


@pytest.fixture()
def vlan(db, nettype):
    vlan = Vlan(vlan="10", net_type=nettype)
    vlan.save()
    yield vlan
    if vlan.pk:
        vlan.delete()


@pytest.fixture()
def prefix(db, vlan):
    prefix = Prefix(net_address='10.1.0.0/16', vlan=vlan)
    prefix.save()
    yield prefix
    if prefix.pk:
        prefix.delete()
