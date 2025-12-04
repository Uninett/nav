from datetime import datetime

import pytest
from django.urls import reverse

from django.utils.encoding import smart_str

from nav.models.event import AlertHistory
from nav.models.manage import Device, Location, Netbox, Room


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


class TestInactiveDeviceHistoryView:
    def test_get_inactive_device_history_should_succeed(self, client, inactive_device):
        url = reverse('devicehistory-view')
        response = client.get(
            f"{url}?from_date=2023-01-01&to_date=2025-01-01&eventtype=all"
            f"&inactive_device={inactive_device.id}",
            follow=True,
        )

        assert response.status_code == 200

    def test_get_inactive_device_history_should_redirect_with_group_by_set_to_device(
        self, client, inactive_device
    ):
        url = reverse('devicehistory-search')
        response = client.get(
            f"{url}?from_date=2023-01-01&eventtype=all"
            f"&inactive_device={inactive_device.id}",
        )
        assert response.status_code == 302
        assert 'group_by=device' in response.url

    def test_given_inactive_device_with_alert_history_then_it_should_return_results(
        self, client, db, inactive_device
    ):
        created_history = create_alert_history_for_device(inactive_device, count=3)

        url = reverse('devicehistory-view')
        response = client.get(
            f"{url}?from_date=2025-01-01&to_date=2025-12-31&eventtype=all&group_by=device"
            f"&inactive_device={inactive_device.id}",
            follow=True,
        )

        assert response.status_code == 200
        response_history = response.context['history']
        assert inactive_device.serial in response_history
        device_history = response_history[inactive_device.serial]
        assert len(device_history) == len(created_history)


def create_alert_history_for_device(device, count=1):
    for day in range(count):
        activity = AlertHistory(
            device=device,
            event_type_id='boxState',
            alert_type_id=1,
            source_id='pping',
            start_time=datetime(2025, 1, day + 1),
            end_time=datetime(2025, 1, day + 10),
            value=42,
        )
        activity.save()
    return AlertHistory.objects.filter(device=device)


@pytest.fixture
def new_room(db):
    location = Location(id="testlocation")
    location.save()
    room = Room(id="123", description="Test Room", location=location)
    room.save()
    yield room
    room.delete()
    location.delete()


@pytest.fixture
def inactive_device(db):
    device = Device(serial="inactivedevice")
    device.save()
    yield device
    device.delete()
