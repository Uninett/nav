# -*- coding: utf-8 -*-
from django.utils.encoding import force_str

from datetime import datetime, timedelta
import json
import pytest
from django.urls import reverse

from nav.models.event import AlertHistory
from nav.models.fields import INFINITY
from nav.web.api.v1.views import get_endpoints
from nav.models.oui import OUI
from nav.models.manage import NetboxEntity


ENDPOINTS = {name: force_str(url) for name, url in get_endpoints().items()}


# Data for writable endpoints

TEST_DATA = {
    'account': {'login': 'testuser', 'name': 'Test User', 'accountgroups': [2, 3]},
    'location': {
        'id': 'Kulsås',
        'data': {'a': 'b'},
        'parent': 'mylocation',
        'description': 'ÆØÅ descr',
    },
    'netbox': {
        "ip": "158.38.152.169",
        "roomid": "myroom",
        "organizationid": "myorg",
        "categoryid": "SW",
        "snmp_version": 2,
    },
    'room': {'id': 'blapp', 'location': 'mylocation'},
    'vlan': {
        'net_type': 'scope',
    },
    'prefix': {'net_address': '158.38.240.0/25'},
}


# Generic tests


@pytest.mark.parametrize("url", ENDPOINTS.values())
def test_forbidden_endpoints(db, api_client, url):
    response = api_client.get(url)
    if url == ENDPOINTS['jwt_refresh']:
        # JWT refresh endpoint only accepts POST requests
        assert response.status_code == 405
    else:
        assert response.status_code == 403


@pytest.mark.parametrize("name, url", ENDPOINTS.items())
def test_allowed_endpoints(db, api_client, token, serializer_models, name, url):
    create_token_endpoint(token, name)
    if name in ['arp', 'cam']:
        # ARP and CAM wants filters
        response = api_client.get("{}?active=1".format(url))
    else:
        response = api_client.get(url)
    if name == 'jwt_refresh':
        # JWT refresh endpoint only accepts POST requests
        assert response.status_code == 405
    else:
        assert response.status_code == 200


@pytest.mark.parametrize("endpoint", ['account', 'location', 'room', 'vlan'])
def test_delete(db, api_client, token, endpoint):
    create_token_endpoint(token, endpoint)
    response_create = create(api_client, endpoint, TEST_DATA.get(endpoint))
    res = json.loads(response_create.content.decode('utf-8'))
    response_delete = delete(api_client, endpoint, res.get('id'))
    response_get = get(api_client, endpoint, res.get('id'))

    print(response_delete)
    assert response_delete.status_code == 204

    print(response_get)
    assert response_get.status_code == 404


@pytest.mark.parametrize("endpoint", ['account', 'netbox', 'location', 'room', 'vlan'])
def test_create(db, api_client, token, endpoint):
    create_token_endpoint(token, endpoint)
    response = create(api_client, endpoint, TEST_DATA.get(endpoint))
    print(response)
    assert response.status_code == 201


def test_page_size(db, api_client, token):
    endpoint = 'room'
    create_token_endpoint(token, endpoint)
    create(api_client, endpoint, {'id': 'blapp1', 'location': 'mylocation'})
    create(api_client, endpoint, {'id': 'blapp2', 'location': 'mylocation'})
    response = api_client.get('/api/1/room/?page_size=1')
    print(response.data)
    assert len(response.data.get('results')) == 1


def test_ordering_should_not_crash(db, api_client, token):
    endpoint = 'room'
    create_token_endpoint(token, endpoint)
    response = api_client.get('/api/1/room/?ordering=whatever')
    print(response.data)
    assert response.status_code == 200


# Account specific tests


def test_update_org_on_account(db, api_client, token):
    endpoint = 'account'
    create_token_endpoint(token, endpoint)
    data = {"organizations": ["myorg"]}
    response = update(api_client, endpoint, 1, data)
    print(response)
    assert response.status_code == 200

    data = {"organizations": []}
    response = update(api_client, endpoint, 1, data)
    print(response)
    assert response.status_code == 200


def test_update_group_on_org(db, api_client, token):
    endpoint = 'account'
    create_token_endpoint(token, endpoint)
    # Only admin group
    data = {"accountgroups": [1]}
    response = update(api_client, endpoint, 1, data)
    print(response)
    assert response.status_code == 200


# Netbox specific tests


def test_filter_netbox_by_invalid_ip(db, api_client, token):
    create_token_endpoint(token, 'netbox')
    response = api_client.get('{}?ip=10'.format(ENDPOINTS['netbox']))
    print(response)
    assert response.status_code == 200


def test_filter_netbox_by_invalid_ip_that_cannot_be_converted_throws_error(
    db, api_client, token
):
    create_token_endpoint(token, 'netbox')
    response = api_client.get('{}?ip=x'.format(ENDPOINTS['netbox']))
    print(response)
    assert response.status_code == 400


def test_update_netbox(db, api_client, token):
    endpoint = 'netbox'
    create_token_endpoint(token, endpoint)
    response_create = create(api_client, endpoint, TEST_DATA.get(endpoint))
    res = json.loads(response_create.content.decode('utf-8'))
    data = {'categoryid': 'GW'}
    response_update = update(api_client, endpoint, res['id'], data)
    print(response_update)
    assert response_update.status_code == 200


def test_delete_netbox(db, api_client, token):
    endpoint = 'netbox'
    create_token_endpoint(token, endpoint)
    response_create = create(api_client, endpoint, TEST_DATA.get(endpoint))
    json_create = json.loads(response_create.content.decode('utf-8'))
    response_delete = delete(api_client, endpoint, json_create['id'])
    response_get = get(api_client, endpoint, json_create['id'])
    json_get = json.loads(response_get.content.decode('utf-8'))

    print(response_delete)
    print(json_get['deleted_at'])

    assert response_delete.status_code == 204
    assert json_get['deleted_at'] is not None


# Room specific tests


def test_get_wrong_room(db, api_client, token):
    create_token_endpoint(token, 'room')
    response = api_client.get('{}blapp/'.format(ENDPOINTS['room']))
    print(response)
    assert response.status_code == 404


def test_get_new_room(db, api_client, token):
    endpoint = 'room'
    create_token_endpoint(token, endpoint)
    create(api_client, endpoint, TEST_DATA.get(endpoint))
    response = api_client.get('/api/1/room/blapp/')
    print(response)
    assert response.status_code == 200


def test_when_room_has_dot_in_id_the_api_should_still_find_it(db, api_client, token):
    create_token_endpoint(token, "room")
    from nav.models.manage import Room

    room = Room(id="foo.bar", location_id="mylocation")
    room.save()

    response = api_client.get(f"/api/1/room/{room.id}/")
    print(response)
    assert response.status_code == 200


def test_when_location_has_dot_in_id_the_api_should_still_find_it(
    db, api_client, token
):
    create_token_endpoint(token, "location")
    from nav.models.manage import Location

    location = Location(id="foo.bar")
    location.save()

    response = api_client.get(f"/api/1/location/{location.id}/")
    print(response)
    assert response.status_code == 200


def test_patch_room_not_found(db, api_client, token):
    create_token_endpoint(token, 'room')
    data = {'location': 'mylocation'}
    response = api_client.patch('/api/1/room/blapp/', data, format='json')
    print(response)
    assert response.status_code == 404


def test_patch_room_wrong_location(db, api_client, token):
    endpoint = 'room'
    create_token_endpoint(token, endpoint)
    create(api_client, endpoint, TEST_DATA.get(endpoint))
    data = {'location': 'mylocatio'}
    response = api_client.patch('/api/1/room/blapp/', data, format='json')
    print(response)
    assert response.status_code == 400


def test_patch_room(db, api_client, token):
    endpoint = 'room'
    create_token_endpoint(token, 'room')
    create(api_client, endpoint, TEST_DATA.get(endpoint))
    data = {'location': 'mylocation'}
    response = api_client.patch('/api/1/room/blapp/', data, format='json')

    print(response)
    assert response.status_code == 200


def test_delete_room_wrong_room(db, api_client, token):
    endpoint = 'room'
    create_token_endpoint(token, 'room')
    create(api_client, endpoint, TEST_DATA.get(endpoint))
    response = api_client.delete('/api/1/room/blap/')

    print(response)
    assert response.status_code == 404


def test_validate_vlan(db, api_client, token):
    endpoint = 'vlan'
    create_token_endpoint(token, 'vlan')
    testdata = dict(TEST_DATA.get(endpoint))
    testdata.update({'net_type': 'core'})
    response = create(api_client, endpoint, testdata)

    print(response)
    assert response.status_code == 400


def prepare_prefix_test(db, api_client, token):
    token.endpoints = {'prefix': ENDPOINTS.get('prefix'), 'vlan': ENDPOINTS.get('vlan')}
    token.save()
    testdata = dict(TEST_DATA.get('prefix'))

    vlan_response = create(api_client, 'vlan', TEST_DATA.get('vlan'))
    vlan = json.loads(vlan_response.content.decode('utf-8'))
    testdata.update({'vlan': vlan.get('id')})
    return testdata


def test_create_prefix(db, api_client, token):
    endpoint = 'prefix'
    testdata = prepare_prefix_test(db, api_client, token)
    response = create(api_client, endpoint, testdata)

    print(response)
    assert response.status_code == 201


def test_create_prefix_with_usage(db, api_client, token, serializer_models):
    endpoint = 'prefix'
    testdata = prepare_prefix_test(db, api_client, token)
    testdata.update({'usages': ['ans']})

    response = create(api_client, endpoint, testdata)
    json_response = json.loads(response.content.decode('utf-8'))
    assert json_response.get('usages') == ['ans']


def test_update_prefix_remove_usage(db, api_client, token, serializer_models):
    endpoint = 'prefix'
    testdata = prepare_prefix_test(db, api_client, token)
    testdata.update({'usages': ['ans', 'student']})
    response = create(api_client, endpoint, testdata)
    prefix = json.loads(response.content.decode('utf-8'))

    testdata.update({'usages': ['ans']})
    response = update(api_client, endpoint, prefix.get('id'), testdata)
    json_response = json.loads(response.content.decode('utf-8'))
    assert json_response.get('usages') == ['ans']


# Alert specific tests


def test_nonexistent_alert_should_give_404(db, api_client, token):
    create_token_endpoint(token, 'alert')
    response = api_client.get('{}9999/'.format(ENDPOINTS['alert']))
    print(response)
    assert response.status_code == 404


def test_alert_should_be_visible_in_api(db, api_client, token, serializer_models):
    create_token_endpoint(token, 'alert')
    alert = AlertHistory.objects.all()[0]
    response = api_client.get('{url}{id}/'.format(url=ENDPOINTS['alert'], id=alert.id))
    print(response)
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    # Simple string tests, but they might just as well parse the JSON structure
    assert str(alert.id) in content
    assert str(alert.netbox.id) in content


# Interface specific tests


def test_interface_with_last_used_should_be_listable(
    db, api_client, token, serializer_models
):
    endpoint = 'interface'
    create_token_endpoint(token, endpoint)
    response = api_client.get('/api/1/interface/?last_used=on')
    print(response.data)
    assert response.status_code == 200


class TestVendorLookupGet:
    def test_if_vendor_is_found_it_should_include_vendor_in_response(
        self, db, api_client, vendor_endpoint, oui
    ):
        test_mac = 'aa:bb:cc:dd:ee:ff'
        response = api_client.get(f"{ENDPOINTS[vendor_endpoint]}?mac={test_mac}")
        assert response.status_code == 200
        assert response.data[test_mac] == oui.vendor

    def test_should_always_return_mac_with_correct_format(
        self, db, api_client, vendor_endpoint, oui
    ):
        test_mac = 'AA-BB-CC-DD-EE-FF'
        response = api_client.get(f"{ENDPOINTS[vendor_endpoint]}?mac={test_mac}")
        assert response.status_code == 200
        assert response.data['aa:bb:cc:dd:ee:ff'] == oui.vendor

    def test_if_vendor_is_not_found_it_should_return_empty_dict(
        self, db, api_client, vendor_endpoint
    ):
        test_mac = 'aa:bb:cc:dd:ee:ff'
        response = api_client.get(f"{ENDPOINTS[vendor_endpoint]}?mac={test_mac}")
        assert response.status_code == 200
        assert response.data == {}

    def test_if_mac_is_invalid_it_should_return_400(
        self, db, api_client, vendor_endpoint
    ):
        test_mac = 'invalidmac'
        response = api_client.get(f"{ENDPOINTS[vendor_endpoint]}?mac={test_mac}")
        assert response.status_code == 400

    def test_if_mac_is_not_provided_it_should_return_empty_dict(
        self, db, api_client, vendor_endpoint
    ):
        response = api_client.get(ENDPOINTS[vendor_endpoint])
        assert response.status_code == 200
        assert response.data == {}


class TestVendorLookupPost:
    def test_if_vendor_is_found_it_should_include_vendor_in_response(
        self, db, api_client, vendor_endpoint, oui
    ):
        test_mac = 'aa:bb:cc:dd:ee:ff'
        response = create(api_client, vendor_endpoint, [test_mac])
        assert response.status_code == 200
        assert response.data[test_mac] == oui.vendor

    def test_should_always_return_macs_with_correct_format(
        self, db, api_client, vendor_endpoint, oui
    ):
        test_mac = 'AA-BB-CC-DD-EE-FF'
        response = create(api_client, vendor_endpoint, [test_mac])
        assert response.status_code == 200
        assert response.data['aa:bb:cc:dd:ee:ff'] == oui.vendor

    def test_if_vendor_is_not_found_it_should_be_omitted_from_response(
        self, db, api_client, vendor_endpoint, oui
    ):
        test_mac = '11:22:33:44:55:66'
        response = create(api_client, vendor_endpoint, [test_mac])
        assert response.status_code == 200
        assert test_mac not in response.data

    def test_if_empty_list_is_provided_it_should_return_empty_dict(
        self, db, api_client, vendor_endpoint
    ):
        response = create(api_client, vendor_endpoint, [])
        assert response.status_code == 200
        assert response.data == {}

    def test_if_mac_is_invalid_it_should_return_400(
        self, db, api_client, vendor_endpoint
    ):
        response = create(api_client, vendor_endpoint, ["invalidmac"])
        assert response.status_code == 400


class TestNetboxEntityViewSet:
    def test_should_return_list_of_entities(
        self, db, api_client, netboxentity_endpoint, netboxentity
    ):
        endpoint = netboxentity_endpoint
        response = get(api_client, endpoint)
        assert response.status_code == 200
        assert response.data['results'][0]['id'] == netboxentity.id

    def test_should_get_correct_entity_when_accessing_with_id(
        self, db, api_client, netboxentity_endpoint, netboxentity
    ):
        endpoint = netboxentity_endpoint
        response = get(api_client, endpoint, id=netboxentity.id)
        assert response.status_code == 200
        assert response.data['id'] == netboxentity.id


# Helpers


def create_token_endpoint(token, name):
    token.endpoints = {name: ENDPOINTS.get(name)}
    token.save()


def get(api_client, endpoint, id=None):
    endpoint = ENDPOINTS[endpoint]
    if id:
        endpoint = endpoint + force_str(id) + '/'
    return api_client.get(endpoint)


def create(api_client, endpoint, data):
    """Sends a post request to endpoint with data"""
    return api_client.post(ENDPOINTS[endpoint], data, format='json')


def update(api_client, endpoint, id, data):
    """Sends a patch request to endpoint with data"""
    return api_client.patch(
        ENDPOINTS[endpoint] + force_str(id) + '/', data, format='json'
    )


def delete(api_client, endpoint, id):
    """Sends a delete request to endpoint"""
    return api_client.delete(ENDPOINTS[endpoint] + force_str(id) + '/')


@pytest.mark.parametrize(
    "urlname, arg",
    [
        ("api:1:alert-detail", 1),
        ("api:1:alert-list", None),
        ("api:1:interface-detail", 1),
        ("api:1:interface-list", None),
        ("api:1:netbox-list", None),
        ("api:1:prefix-usage-list", None),
        ("api:1:rack-detail", 1),
        ("api:1:room-list", None),
    ],
)
def test_api_urls_should_resolve(urlname, arg):
    """Regression test to verify that the view names generated by Django REST framework
    are still valid.
    """
    if arg is None:
        assert reverse(urlname)
    else:
        assert reverse(urlname, args=(arg,))


# Fixtures


@pytest.fixture()
def serializer_models(localhost, admin_account):
    """Fixture for testing API serializers

    - unrecognized_neighbor
    - auditlog
    """
    from nav.models import cabling, event, manage, rack
    from nav.auditlog import models as auditlog

    netbox = localhost

    group = manage.NetboxGroup.objects.all()[0]
    manage.NetboxCategory(netbox=netbox, category=group).save()

    interface = manage.Interface(
        netbox=netbox, ifindex=1, ifname='if1', ifdescr='ifdescr', iftype=1, speed=10
    )
    interface.save()
    manage.Cam(
        sysname='asd', mac='aa:aa:aa:aa:aa:aa', ifindex=1, end_time=datetime.now()
    ).save()
    manage.Arp(
        sysname='asd',
        mac='aa:bb:cc:dd:ee:ff',
        ip='123.123.123.123',
        end_time=datetime.now(),
    ).save()
    manage.Prefix(net_address='123.123.123.123').save()
    manage.Vlan(vlan=10, net_type_id='lan').save()
    rack.Rack(room_id='myroom').save()
    cabel = cabling.Cabling(room_id='myroom', jack='1')
    cabel.save()
    cabling.Patch(interface=interface, cabling=cabel).save()

    source = event.Subsystem.objects.get(pk='pping')
    target = event.Subsystem.objects.get(pk='eventEngine')
    event_type = event.EventType.objects.get(pk='boxState')

    boxdown_id = 3

    event.EventQueue(
        source=source, target=target, event_type=event_type, netbox=netbox
    ).save()
    event.AlertHistory(
        source=source,
        event_type=event_type,
        netbox=netbox,
        start_time=datetime.now() - timedelta(days=1),
        value=1,
        severity=3,
        alert_type_id=boxdown_id,
        end_time=INFINITY,
    ).save()
    auditlog.LogEntry.add_log_entry(admin_account, verb='verb', template='asd')
    manage.Usage(id='ans', description='Ansatte').save()
    manage.Usage(id='student', description='Studenter').save()


@pytest.fixture()
def oui(db):
    oui = OUI(oui='aa:bb:cc:00:00:00', vendor='myvendor')
    oui.save()
    yield oui
    oui.delete()


@pytest.fixture()
def vendor_endpoint(db, token):
    endpoint = 'vendor'
    create_token_endpoint(token, endpoint)
    return endpoint


@pytest.fixture()
def netboxentity_endpoint(db, token):
    endpoint = 'netboxentity'
    create_token_endpoint(token, endpoint)
    return endpoint


@pytest.fixture()
def netboxentity(db, localhost):
    netbox_entity = NetboxEntity(netbox=localhost, index=0)
    netbox_entity.save()
    yield netbox_entity
    netbox_entity.delete()
