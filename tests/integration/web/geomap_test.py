from django.db import connection

import nav.db


DATA_URL = (
    '/geomap/normal/data?format=geojson&limit=30&viewportWidth=1789'
    '&viewportHeight=817&create_edges=true&fetch_data=true'
    '&timeStart=10%3A10_20181109&timeEnd=10%3A20_20181109'
    '&bbox=10.381361116473,63.411482408125,10.419748891889,63.419327821103'
)


def test_geomap_data_should_not_crash(client):
    response = client.get(DATA_URL)
    assert response.status_code == 200


def test_geomap_data_should_leave_django_connection_in_autocommit(client):
    response = client.get(DATA_URL)
    assert response.status_code == 200
    # The view must not flip autocommit/isolation on the raw connection,
    # which would leave the thread's connection idle in a transaction.
    assert connection.get_autocommit()


def test_geomap_data_should_not_use_legacy_nav_db_cache(client):
    before = len(list(nav.db._connection_cache.values()))
    response = client.get(DATA_URL)
    assert response.status_code == 200
    assert len(list(nav.db._connection_cache.values())) == before
