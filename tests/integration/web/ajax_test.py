from django.urls import reverse


def test_neighbormap_loads_without_crashing(db, localhost, client):
    url = reverse("ajax-get-neighbors", args=(localhost.pk,))
    response = client.get(url)
    assert response.status_code == 200
