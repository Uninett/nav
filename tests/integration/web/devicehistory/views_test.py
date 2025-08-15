import pytest
from django.urls import reverse

from django.utils.encoding import smart_str
from nav.models.manage import Netbox, Room, Location


class TestSearchDeviceHistoryComponents:
    def test_given_an_existing_room_then_component_search_should_return_results(
        self, db, client, new_room
    ):
        url = reverse('devicehistory-component-search')
        response = client.post(url, {'search': new_room.id})
        assert response.status_code == 200
        assert new_room.id in smart_str(response.content)

    def test_given_a_non_existing_component_then_component_search_should_return_no_hits(
        self, client
    ):
        url = reverse('devicehistory-component-search')
        response = client.post(url, {'search': 'nonexistent-component'})
        assert response.status_code == 200
        assert "No hits" in smart_str(response.content)

    def test_given_an_empty_query_then_component_search_should_return_no_hits(
        self, client
    ):
        url = reverse('devicehistory-component-search')
        response = client.post(url, {'search': ''})
        assert response.status_code == 200
        assert "No hits" in smart_str(response.content)


class TestSearchDeviceHistoryRegisterErrorComponents:
    def test_given_an_existing_netbox_then_component_search_should_return_results(
        self, db, client
    ):
        url = reverse('devicehistory-registererror-component-search')
        netbox = Netbox.objects.first()
        response = client.post(url, {'search': netbox.sysname})
        assert response.status_code == 200
        assert netbox.sysname in smart_str(response.content)

    def test_given_a_non_existing_component_then_component_search_should_return_no_hits(
        self, client
    ):
        url = reverse('devicehistory-registererror-component-search')
        response = client.post(url, {'search': 'nonexistent-component'})
        assert response.status_code == 200
        assert "No hits" in smart_str(response.content)

    def test_given_an_empty_query_then_component_search_should_return_no_hits(
        self, client
    ):
        url = reverse('devicehistory-registererror-component-search')
        response = client.post(url, {'search': ''})
        assert response.status_code == 200
        assert "No hits" in smart_str(response.content)


class TestDeviceHistorySearch:
    def test_when_query_parameter_is_empty_then_return_search_page(self, client):
        url = reverse('devicehistory-search')
        response = client.get(url)
        assert response.status_code == 200
        assert 'Search' in smart_str(response.content)

    def test_when_from_date_is_set_then_return_search_results(self, client):
        url = reverse('devicehistory-search') + '?from_date=2023-01-01'
        response = client.get(url)
        assert response.status_code == 200
        assert 'id="device-history-search-results"' in smart_str(response.content)


class TestRegisterError:
    def test_when_no_devices_are_selected_then_return_error_message(self, client):
        url = reverse('devicehistory-do-registererror')
        response = client.post(url, follow=True)
        assert response.status_code == 200
        assert "No devices selected" in smart_str(response.content)

    def test_when_devices_are_selected_then_show_selected_devices(
        self, client, localhost
    ):
        url = reverse('devicehistory-do-registererror')
        response = client.post(url, data={'netbox': [localhost.id]}, follow=True)
        assert response.status_code == 200
        assert localhost.sysname in smart_str(response.content)

    def test_when_no_error_comment_supplied_then_require_confirmation(
        self, client, localhost
    ):
        url = reverse('devicehistory-do-registererror')
        response = client.post(
            url, data={'netbox': [localhost.id], 'error_comment': ''}, follow=True
        )
        assert response.status_code == 200
        assert "Confirm" in smart_str(response.content)

    def test_when_selected_devices_and_error_comment_supplied_then_register_error(
        self, client, localhost
    ):
        url = reverse('devicehistory-do-registererror')
        response = client.post(
            url,
            data={'netbox': [localhost.id], 'error_comment': 'Test error'},
            follow=True,
        )
        assert response.status_code == 200
        assert "Registered error" in smart_str(response.content)


@pytest.fixture
def new_room(db):
    location = Location(id="testlocation")
    location.save()
    room = Room(id="123", description="Test Room", location=location)
    room.save()
    yield room
    room.delete()
    location.delete()
