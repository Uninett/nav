import pytest
from django.urls import reverse
from django.utils.encoding import smart_str

from nav.models.manage import Location, Room


class TestRoomNetboxInterfacesView:
    def test_should_render_about_search_modal_trigger(self, client, new_room):
        url = reverse('room-info-netboxes', args=[new_room.id])
        modal_url = reverse('room-info-about-the-search')
        response = client.get(url)
        assert response.status_code == 200
        assert f'hx-get="{modal_url}' in smart_str(response.content)

    def test_should_render_about_search_modal(self, client):
        url = reverse('room-info-about-the-search')
        response = client.get(url)
        assert response.status_code == 200
        assert 'id="about-the-search"' in smart_str(response.content)


@pytest.fixture
def new_room(db):
    location = Location(id="testlocation")
    location.save()
    room = Room(id="123", description="Test Room", location=location)
    room.save()
    yield room
    room.delete()
    location.delete()
