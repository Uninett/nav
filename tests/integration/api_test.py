from __future__ import print_function
from django.utils.encoding import force_text

import json
import pytest

from nav.web.api.v1.views import get_endpoints


ENDPOINTS = { name:force_text(url) for name, url in get_endpoints().items() }


def create_token_endpoint(token, name):
    token.endpoints = {name: ENDPOINTS.get(name)}
    token.save()


def get(api_client, endpoint, id=None):
    endpoint = ENDPOINTS[endpoint]
    if id:
        endpoint = endpoint + force_text(id) + '/'
    return api_client.get(endpoint)


def create(api_client, endpoint, data):
    """Sends a post request to endpoint with data"""
    return api_client.post(ENDPOINTS[endpoint], data, format='json')


def update(api_client, endpoint, id, data):
    """Sends a patch request to endpoint with data"""
    return api_client.patch(ENDPOINTS[endpoint] + force_text(id) + '/', data, format='json')


def delete(api_client, endpoint, id):
    """Sends a delete request to endpoint"""
    return api_client.delete(ENDPOINTS[endpoint] + force_text(id) + '/')


# Generic tests

@pytest.mark.parametrize("url", ENDPOINTS.values())
def test_forbidden_endpoints(db, api_client, url):
    response = api_client.get(url)
    assert response.status_code == 403


@pytest.mark.parametrize("name, url", ENDPOINTS.items())
def test_allowed_endpoints(db, api_client, token, serializer_models, name, url):
    create_token_endpoint(token, name)
    if name in ['arp', 'cam']:
        # ARP and CAM wants filters
        response = api_client.get("{}?active=1".format(url))
    else:
        response = api_client.get(url)
    assert response.status_code == 200


# Data for writable endpoints

_account_data = {'login': 'testuser',
                 'name': 'Test User',
                 'accountgroups': [2, 3]}
_netbox_data = {
    "ip": "158.38.152.169",
    "roomid": "myroom",
    "organizationid": "myorg",
    "categoryid": "SW",
    "snmp_version": 2
}
_room_data = {'id': 'blapp', 'location': 'mylocation'}


# Account specific tests

def test_create_account(db, api_client, token):
    endpoint = 'account'
    create_token_endpoint(token, endpoint)
    response = create(api_client, endpoint, _account_data)
    print(response)
    assert response.status_code == 201


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


def test_delete_account(db, api_client, token):
    endpoint = 'account'
    create_token_endpoint(token, endpoint)
    response_create = create(api_client, endpoint, _account_data)
    res = json.loads(response_create.content.decode('utf-8'))
    response_delete = delete(api_client, endpoint, res.get('id'))
    response_get = get(api_client, endpoint, res.get('id'))

    print(response_delete)
    assert response_delete.status_code == 204

    print(response_get)
    assert response_get.status_code == 404


# Netbox specific tests

def test_create_netbox(db, api_client, token):
    endpoint = 'netbox'
    create_token_endpoint(token, endpoint)
    response = create(api_client, endpoint, _netbox_data)
    print(response)
    assert response.status_code == 201


def test_update_netbox(db, api_client, token):
    endpoint = 'netbox'
    create_token_endpoint(token, endpoint)
    response_create = create(api_client, endpoint, _netbox_data)
    res = json.loads(response_create.content.decode('utf-8'))
    data = {'categoryid': 'GW'}
    response_update = update(api_client, endpoint, res['id'], data)
    print(response_update)
    assert response_update.status_code == 200


def test_delete_netbox(db, api_client, token):
    endpoint = 'netbox'
    create_token_endpoint(token, endpoint)
    response_create = create(api_client, endpoint, _netbox_data)
    json_create = json.loads(response_create.content.decode('utf-8'))
    response_delete = delete(api_client, endpoint, json_create['id'])
    response_get = get(api_client, endpoint, json_create['id'])
    json_get = json.loads(response_get.content.decode('utf-8'))

    print(response_delete)
    print(json_get['deleted_at'])

    assert response_delete.status_code == 204
    assert json_get['deleted_at'] != None


# Room specific tests


def test_get_wrong_room(db, api_client, token):
    create_token_endpoint(token, 'room')
    response = api_client.get('{}blapp/'.format(ENDPOINTS['room']))
    print(response)
    assert response.status_code == 404


def test_create_new_room(db, api_client, token):
    endpoint = 'room'
    create_token_endpoint(token, endpoint)
    response = create(api_client, endpoint, _room_data)
    print(response)
    assert response.status_code == 201


def test_get_new_room(db, api_client, token):
    endpoint = 'room'
    create_token_endpoint(token, endpoint)
    create(api_client, endpoint, _room_data)
    response = api_client.get('/api/1/room/blapp/')
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
    create(api_client, endpoint, _room_data)
    data = {'location': 'mylocatio'}
    response = api_client.patch('/api/1/room/blapp/', data, format='json')
    print(response)
    assert response.status_code == 400


def test_patch_room(db, api_client, token):
    endpoint = 'room'
    create_token_endpoint(token, 'room')
    create(api_client, endpoint, _room_data)
    data = {'location': 'mylocation'}
    response = api_client.patch('/api/1/room/blapp/', data, format='json')

    print(response)
    assert response.status_code == 200


def test_delete_room_wrong_room(db, api_client, token):
    endpoint = 'room'
    create_token_endpoint(token, 'room')
    create(api_client, endpoint, _room_data)
    response = api_client.delete('/api/1/room/blap/')

    print(response)
    assert response.status_code == 404


def test_delete_room(db, api_client, token):
    endpoint = 'room'
    create_token_endpoint(token, 'room')
    create(api_client, endpoint, _room_data)
    response1 = delete(api_client, endpoint, 'blapp')
    response2 = get(api_client, endpoint, 'blapp')

    print(response1)
    assert response1.status_code == 204

    print(response2)
    assert response2.status_code == 404
