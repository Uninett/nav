from nav.bootstrap import bootstrap_django
bootstrap_django(__file__)


ENDPOINTS = {
    'room': '/api/1/room/'
}

ENDPOINTS2 = {
    "arp": "/api/1/arp/",
    "account": "/api/1/account/",
    "prefix_routed": "/api/1/prefix/routed",
    "room": "/api/1/room/",
    "unrecognized_neighbor": "/api/1/unrecognized-neighbor/",
    "cabling": "/api/1/cabling/",
    "vlan": "/api/1/vlan/",
    "netbox": "/api/1/netbox/",
    "accountgroup": "/api/1/accountgroup/",
    "alert": "/api/1/alert/",
    "prefix_usage": "/api/1/prefix/usage",
    "prefix": "/api/1/prefix/",
    "cam": "/api/1/cam/",
    "interface": "/api/1/interface/",
    "servicehandler": "/api/1/servicehandler/",
    "patch": "/api/1/patch/",
    "auditlog": "/api/1/auditlog/",
    "rack": "/api/1/rack/"
}


def create_token_endpoint(token, name):
    token.endpoints = {name: ENDPOINTS.get(name)}
    token.save()


def test_forbidden_endpoints(db, api_client):
    for url in ENDPOINTS.values():
        response = api_client.get(url)
        assert response.status_code == 403


def test_allowed_endpoints(db, api_client, token):
    for name, url in ENDPOINTS.items():
        create_token_endpoint(token, name)
        response = api_client.get(url)
        assert response.status_code == 200


def test_get_wrong_room(db, api_client, token):
    create_token_endpoint(token, 'room')
    response = api_client.get('/api/1/room/blapp/')
    print response
    assert response.status_code == 404


def test_create_new_room(db, api_client, token):
    create_token_endpoint(token, 'room')
    data = {'id': 'blapp', 'location': 'mylocation'}
    response = api_client.post('/api/1/room/', data, format='json')
    print response
    assert response.status_code == 201


def test_get_new_room(db, api_client, token):
    create_token_endpoint(token, 'room')
    data = {'id': 'blapp', 'location': 'mylocation'}
    _response = api_client.post('/api/1/room/', data, format='json')
    response = api_client.get('/api/1/room/blapp/')
    print response
    assert response.status_code == 200


def test_patch_room_not_found(db, api_client, token):
    create_token_endpoint(token, 'room')
    data = {'location': 'mylocation'}
    response = api_client.patch('/api/1/room/blapp/', data, format='json')
    print response
    assert response.status_code == 404


def test_patch_room_wrong_location(db, api_client, token):
    create_token_endpoint(token, 'room')
    data = {'id': 'blapp', 'location': 'mylocation'}
    response = api_client.post('/api/1/room/', data, format='json')

    data = {'location': 'mylocatio'}
    response = api_client.patch('/api/1/room/blapp/', data, format='json')

    print response
    assert response.status_code == 400


def test_patch_room(db, api_client, token):
    create_token_endpoint(token, 'room')
    data = {'id': 'blapp', 'location': 'mylocation'}
    response = api_client.post('/api/1/room/', data, format='json')

    data = {'location': 'mylocation'}
    response = api_client.patch('/api/1/room/blapp/', data, format='json')

    print response
    assert response.status_code == 200


def test_delete_room_wrong_room(db, api_client, token):
    create_token_endpoint(token, 'room')
    data = {'id': 'blapp', 'location': 'mylocation'}
    response = api_client.post('/api/1/room/', data, format='json')
    response = api_client.delete('/api/1/room/blap/')

    print response
    assert response.status_code == 404


def test_delete_room(db, api_client, token):
    create_token_endpoint(token, 'room')
    data = {'id': 'blapp', 'location': 'mylocation'}
    response = api_client.post('/api/1/room/', data, format='json')
    response1 = api_client.delete('/api/1/room/blapp/')
    response2 = api_client.get('/api/1/room/blapp/')

    print response1
    assert response1.status_code == 204

    print response2
    assert response2.status_code == 404
