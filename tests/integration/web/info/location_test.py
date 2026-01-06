import pytest
from django.urls import reverse
from django.utils.encoding import smart_str

from nav.models.manage import Location


class TestLocationInfoView:
    def test_location_info_url_should_allow_slashes(self, client, location_with_slash):
        url = reverse('location-info', args=[location_with_slash.id])
        response = client.get(url)
        assert response.status_code == 200
        assert location_with_slash.id in smart_str(response.content)

    def test_location_info_upload_url_should_allow_slashes(
        self, client, location_with_slash
    ):
        url = reverse('location-info-upload', args=[location_with_slash.id])
        response = client.get(url)
        assert response.status_code == 200
        assert location_with_slash.id in smart_str(response.content)


@pytest.fixture
def location_with_slash(db):
    location = Location.objects.create(id='TEST/SLASH')
    yield location
    location.delete()
