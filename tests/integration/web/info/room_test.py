import pytest
from django.test import Client
from django.urls import reverse
from django.utils.encoding import smart_str

from nav.models.manage import Location, Room
from nav.models.profiles import Account


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


class TestAddRoomRackViews:
    def test_should_render_add_rack_modal_trigger(self, client, new_room):
        url = reverse('room-info-racks', args=[new_room.id])
        modal_url = reverse('room-info-racks-add-rack-modal', args=[new_room.id])
        response = client.get(url)
        assert response.status_code == 200
        assert f'hx-get="{modal_url}' in smart_str(response.content)

    def test_should_render_add_rack_modal(self, client, new_room):
        url = reverse('room-info-racks-add-rack-modal', args=[new_room.id])
        response = client.get(url)
        assert response.status_code == 200
        assert 'id="add-rack-modal"' in smart_str(response.content)

    def test_when_account_is_not_admin_then_return_403(
        self, non_admin_client, new_room
    ):
        url = reverse('room-info-racks-add-rack', args=[new_room.id])
        response = non_admin_client.post(url, {'rackname': 'Test Rack'})
        assert response.status_code == 403

    def test_when_account_is_admin_then_add_rack(self, client, new_room):
        url = reverse('room-info-racks-add-rack', args=[new_room.id])
        response = client.post(url, {'rackname': 'Test Rack'})
        assert response.status_code == 200
        assert 'Test Rack' in smart_str(response.content)

    def test_when_rack_is_added_then_return_template_with_editmode(
        self, client, new_room
    ):
        url = reverse('room-info-racks-add-rack', args=[new_room.id])
        response = client.post(
            url,
            {
                'rackname': 'Test Rack',
            },
        )
        assert response.status_code == 200
        assert 'class="rack editmode"' in smart_str(response.content)

    def test_when_rack_is_added_then_return_color_chooser_options(
        self, client, new_room
    ):
        url = reverse('room-info-racks-add-rack', args=[new_room.id])
        response = client.post(
            url,
            {
                'rackname': 'Test Rack',
            },
        )
        assert response.status_code == 200
        assert 'name="rack-color"' in smart_str(response.content)


@pytest.fixture
def new_room(db):
    location = Location(id="testlocation")
    location.save()
    room = Room(id="123", description="Test Room", location=location)
    room.save()
    yield room
    room.delete()
    location.delete()


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
