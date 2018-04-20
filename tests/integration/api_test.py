from nav.bootstrap import bootstrap_django
bootstrap_django(__file__)


def test_forbidden_room_endpoint(api_client):
    response = api_client.get('/api/1/room/')
    assert response.status_code == 403
