from nav.bootstrap import bootstrap_django
bootstrap_django(__file__)


def test_forbidden_room_endpoint(db, api_client):
    response = api_client.get('/api/1/room/')
    assert response.status_code == 403


def test_allowed_room_endpoint(db, api_client, token):
    token.endpoints = {
        'room': '/api/1/room/'
    }
    token.save()

    response = api_client.get('/api/1/room/')
    assert response.status_code == 200


def test_get_wrong_room(db, api_client, token):
    token.endpoints = {
        'room': '/api/1/room/'
    }
    token.save()

    response = api_client.get('/api/1/room/blapp/')
    print response
    assert response.status_code == 404


def test_create_new_room(db, api_client, token):
    token.endpoints = {
        'room': '/api/1/room/'
    }
    token.save()

    data = {'id': 'blapp', 'location': 'mylocation'}
    response = api_client.post('/api/1/room/', data, format='json')
    print response
    assert response.status_code == 201


def test_get_new_room(db, api_client, token):
    token.endpoints = {
        'room': '/api/1/room/'
    }
    token.save()

    data = {'id': 'blapp', 'location': 'mylocation'}
    _response = api_client.post('/api/1/room/', data, format='json')
    response = api_client.get('/api/1/room/blapp/')
    print response
    assert response.status_code == 200


def test_patch_room_not_found(db, api_client, token):
    token.endpoints = {
        'room': '/api/1/room/'
    }
    token.save()

    data = {'location': 'mylocation'}
    response = api_client.patch('/api/1/room/blapp/', data, format='json')
    print response
    assert response.status_code == 404


def test_patch_room_wrong_location(db, api_client, token):
    token.endpoints = {
        'room': '/api/1/room/'
    }
    token.save()

    data = {'id': 'blapp', 'location': 'mylocation'}
    response = api_client.post('/api/1/room/', data, format='json')

    data = {'location': 'mylocatio'}
    response = api_client.patch('/api/1/room/blapp/', data, format='json')

    print response
    assert response.status_code == 400


def test_patch_room(db, api_client, token):
    token.endpoints = {
        'room': '/api/1/room/'
    }
    token.save()

    data = {'id': 'blapp', 'location': 'mylocation'}
    response = api_client.post('/api/1/room/', data, format='json')

    data = {'location': 'mylocation'}
    response = api_client.patch('/api/1/room/blapp/', data, format='json')

    print response
    assert response.status_code == 200


def test_delete_room_wrong_room(db, api_client, token):
    token.endpoints = {
        'room': '/api/1/room/'
    }
    token.save()

    data = {'id': 'blapp', 'location': 'mylocation'}
    response = api_client.post('/api/1/room/', data, format='json')
    response = api_client.delete('/api/1/room/blap/')

    print response
    assert response.status_code == 404


def test_delete_room(db, api_client, token):
    token.endpoints = {
        'room': '/api/1/room/'
    }
    token.save()

    data = {'id': 'blapp', 'location': 'mylocation'}
    response = api_client.post('/api/1/room/', data, format='json')
    response1 = api_client.delete('/api/1/room/blapp/')
    response2 = api_client.get('/api/1/room/blapp/')

    print response1
    assert response1.status_code == 204

    print response2
    assert response2.status_code == 404
