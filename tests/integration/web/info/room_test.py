import pytest
from django.urls import reverse
from django.utils.encoding import smart_str

from nav.models.manage import Room, Sensor
from nav.models.profiles import Account
from nav.models.rack import Rack
from nav.web.info.room.views import ADD_SENSOR_MODAL_ID


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
    room = Room(id="myroom", description="Test Room", location_id="mylocation")
    yield room
    room.delete()


@pytest.fixture
def test_rack(db, test_sensor):
    rack = Rack(room=test_sensor.netbox.room, rackname="Test Rack")
    rack.save()
    yield rack
    rack.delete()


@pytest.fixture
def test_sensor(db, localhost):
    sensor = Sensor(
        netbox=localhost, oid="1.2.3", unit_of_measurement=Sensor.UNIT_CELSIUS
    )
    sensor.save()
    yield sensor
    sensor.delete()


NON_ADMIN_PASSWORD = "avalidpassword"


@pytest.fixture
def non_admin_account(db):
    account = Account.objects.create(login="testuser", password=NON_ADMIN_PASSWORD)
    yield account
    account.delete()


@pytest.fixture(scope='function')
def non_admin_client(client, non_admin_account):
    client_ = Client()
    url = reverse('webfront-login')
    client_.post(
        url, {'username': non_admin_account.login, 'password': NON_ADMIN_PASSWORD}
    )
    return client_
