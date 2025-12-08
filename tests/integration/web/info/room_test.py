import pytest
from django.test import Client
from django.urls import reverse
from django.utils.encoding import smart_str

from nav.models.manage import Room, Sensor
from nav.models.rack import Rack
from nav.web.info.room.views import ADD_SENSOR_MODAL_ID


class TestRoomInfoView:
    def test_room_info_url_should_allow_slashes(self, client, room_with_slash):
        url = reverse('room-info', args=[room_with_slash.id])
        response = client.get(url)
        assert response.status_code == 200
        assert room_with_slash.id in smart_str(response.content)


class TestRoomNetboxInterfacesView:
    def test_should_render_about_search_modal_trigger(self, client):
        url = reverse('room-info-netboxes', args=['myroom'])
        modal_url = reverse('room-info-about-the-search')
        response = client.get(url)
        assert response.status_code == 200
        assert f'hx-get="{modal_url}' in smart_str(response.content)

    def test_should_render_about_search_modal(self, client):
        url = reverse('room-info-about-the-search')
        response = client.get(url)
        assert response.status_code == 200
        assert 'id="about-the-search"' in smart_str(response.content)


class TestAddRoomRackViews:
    def test_should_render_add_rack_modal_trigger(self, client):
        url = reverse('room-info-racks', args=['myroom'])
        modal_url = reverse('room-info-racks-add-rack-modal', args=['myroom'])
        response = client.get(url)
        assert response.status_code == 200
        assert f'hx-get="{modal_url}' in smart_str(response.content)

    def test_should_render_add_rack_modal(self, client):
        url = reverse('room-info-racks-add-rack-modal', args=['myroom'])
        response = client.get(url)
        assert response.status_code == 200
        assert 'id="add-rack-modal"' in smart_str(response.content)

    def test_when_account_is_not_admin_then_return_403(self, non_admin_client):
        url = reverse('room-info-racks-add-rack', args=['myroom'])
        response = non_admin_client.post(url, {'rackname': 'Test Rack'})
        assert response.status_code == 403

    def test_when_account_is_admin_then_add_rack(self, client):
        url = reverse('room-info-racks-add-rack', args=['myroom'])
        response = client.post(url, {'rackname': 'Test Rack'})
        assert response.status_code == 200
        assert 'Test Rack' in smart_str(response.content)

    def test_when_rack_is_added_then_return_template_with_editmode(self, client):
        url = reverse('room-info-racks-add-rack', args=['myroom'])
        response = client.post(
            url,
            {
                'rackname': 'Test Rack',
            },
        )
        assert response.status_code == 200
        assert 'class="rack editmode"' in smart_str(response.content)

    def test_when_rack_is_added_then_return_color_chooser_options(self, client):
        url = reverse('room-info-racks-add-rack', args=['myroom'])
        response = client.post(
            url,
            {
                'rackname': 'Test Rack',
            },
        )
        assert response.status_code == 200
        assert 'name="rack-color"' in smart_str(response.content)

    def test_when_rack_is_added_then_return_rack_added_event(self, client):
        url = reverse('room-info-racks-add-rack', args=['myroom'])
        response = client.post(
            url,
            {
                'rackname': 'Test Rack',
            },
        )
        assert response.status_code == 200
        assert 'room.rack.added' in response.headers['HX-Trigger']

    def test_should_add_rack_for_room_id_with_slash(self, client, room_with_slash):
        url = reverse('room-info-racks-add-rack', args=[room_with_slash.id])
        response = client.get(url)
        assert response.status_code == 200
        assert 'room.rack.added' in response.headers['HX-Trigger']


class TestAddSensorModalView:
    def test_should_render_add_sensor_modal(self, client, test_rack):
        url = reverse('room-info-racks-add-sensor-modal', args=[test_rack.room.id])
        response = client.post(url, data={'rackid': test_rack.id, 'column': 1})
        assert response.status_code == 200
        assert f'id="{ADD_SENSOR_MODAL_ID}"' in smart_str(response.content)

    def test_should_render_modal_with_rackid(self, client, test_rack):
        url = reverse('room-info-racks-add-sensor-modal', args=[test_rack.room.id])
        response = client.post(url, data={'rackid': test_rack.id, 'column': 1})
        assert response.status_code == 200
        assert f'name="rackid" value="{test_rack.id}"' in smart_str(response.content)

    def test_should_render_modal_with_column(self, client, test_rack):
        url = reverse('room-info-racks-add-sensor-modal', args=[test_rack.room.id])
        response = client.post(url, data={'rackid': test_rack.id, 'column': 1})
        assert response.status_code == 200
        assert 'name="column" value="1"' in smart_str(response.content)

    def test_given_no_rackid_then_return_400(self, client):
        url = reverse('room-info-racks-add-sensor-modal', args=['myroom'])
        response = client.post(url, data={'column': 1})
        assert response.status_code == 400

    def test_given_invalid_column_then_return_400(self, client, test_rack):
        url = reverse('room-info-racks-add-sensor-modal', args=[test_rack.room.id])
        response = client.post(url, data={'rackid': test_rack.id, 'column': '-1'})
        assert response.status_code == 400

    def test_given_non_existing_roomid_then_return_404(self, client, test_rack):
        url = reverse('room-info-racks-add-sensor-modal', args=[999])
        response = client.post(url, data={'rackid': test_rack.id, 'column': 1})
        assert response.status_code == 404

    def test_given_non_existing_rackid_then_return_404(self, client):
        url = reverse('room-info-racks-add-sensor-modal', args=['myroom'])
        response = client.post(url, data={'column': 1, 'rackid': 999})
        assert response.status_code == 404


class TestSaveSensorView:
    def test_when_saving_single_sensor_then_return_rack_item(
        self, client, test_rack, test_sensor
    ):
        url = reverse('room-info-racks-save-sensor', args=['myroom'])
        response = client.post(
            url,
            {
                'item_type': 'Sensor',
                'sensorid': test_sensor.id,
                'rackid': test_rack.id,
                'column': 1,
            },
        )
        assert f'id="item_{test_rack.id}_' in smart_str(response.content)

    def test_when_saving_sensor_diff_then_return_rack_item(
        self, db, client, test_rack, test_sensor
    ):
        # Create another sensor for diff
        sensor2 = Sensor.objects.create(
            netbox=test_sensor.netbox,
            oid="1.2.4",
            unit_of_measurement=test_sensor.unit_of_measurement,
        )
        url = reverse('room-info-racks-save-sensor', args=['myroom'])
        response = client.post(
            url,
            {
                'item_type': 'SensorsDiff',
                'minuendid': test_sensor.id,
                'subtrahendid': sensor2.id,
                'rackid': test_rack.id,
                'column': 1,
            },
        )
        assert f'id="item_{test_rack.id}_' in smart_str(response.content)

    def test_when_saving_sensor_sum_then_return_rack_item(
        self, db, client, test_rack, test_sensor
    ):
        # Create two more sensors for sum
        sensor2 = Sensor.objects.create(
            netbox=test_sensor.netbox,
            oid="1.2.5",
            unit_of_measurement=test_sensor.unit_of_measurement,
        )
        sensor3 = Sensor.objects.create(
            netbox=test_sensor.netbox,
            oid="1.2.6",
            unit_of_measurement=test_sensor.unit_of_measurement,
        )
        url = reverse('room-info-racks-save-sensor', args=['myroom'])
        response = client.post(
            url,
            {
                'item_type': 'SensorsSum',
                'sensors[]': [test_sensor.id, sensor2.id, sensor3.id],
                'title': 'Sum Test',
                'rackid': test_rack.id,
                'column': 1,
            },
        )
        assert f'id="item_{test_rack.id}_' in smart_str(response.content)

    def test_given_missing_sensorid_when_saving_sensor_then_return_error(
        self, client, test_rack
    ):
        url = reverse('room-info-racks-save-sensor', args=['myroom'])
        response = client.post(
            url,
            {
                'item_type': 'Sensor',
                'rackid': test_rack.id,
                'column': 1,
            },
        )
        assert response.status_code == 200
        assert b'No sensor selected' in response.content

    def test_given_missing_subtrahend_when_saving_sensor_diff_then_return_error(
        self, client, test_rack, test_sensor
    ):
        url = reverse('room-info-racks-save-sensor', args=['myroom'])
        response = client.post(
            url,
            {
                'item_type': 'SensorsDiff',
                'minuendid': test_sensor.id,
                'rackid': test_rack.id,
                'column': 1,
            },
        )
        assert response.status_code == 200
        assert b'Two sensors must be selected' in response.content

    def test_given_invalid_sum_data_when_saving_sensor_sum_then_return_error(
        self, client, test_rack, test_sensor
    ):
        url = reverse('room-info-racks-save-sensor', args=['myroom'])
        response = client.post(
            url,
            {
                'item_type': 'SensorsSum',
                'sensors[]': [test_sensor.id],
                'title': '',
                'rackid': test_rack.id,
                'column': 1,
            },
        )
        assert response.status_code == 200
        assert (
            b'At least two sensors must be selected and a title given'
            in response.content
        )


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


@pytest.fixture(scope='function')
def non_admin_client(client, non_admin_account):
    client_ = Client()
    url = reverse('webfront-login')
    client_.post(url, {'username': non_admin_account.login, 'password': 'password'})
    return client_


@pytest.fixture
def room_with_slash(db):
    room = Room.objects.create(id='TEST/SLASH', location_id='mylocation')
    yield room
    room.delete()
