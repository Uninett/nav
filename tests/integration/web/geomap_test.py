def test_geomap_data_should_not_crash(client):
    url = (
        '/geomap/normal/data?format=geojson&limit=30&viewportWidth=1789'
        '&viewportHeight=817&create_edges=true&fetch_data=true'
        '&timeStart=10%3A10_20181109&timeEnd=10%3A20_20181109'
        '&bbox=10.381361116473,63.411482408125,10.419748891889,63.419327821103'
    )
    response = client.get(url)
    assert response.status_code == 200
