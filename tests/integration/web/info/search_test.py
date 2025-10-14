# -*- coding: utf-8 -*-
from django.urls import reverse

from nav.models.manage import Interface


def test_search_for_ip_devices_should_not_crash(client):
    url = reverse('info-search') + '?query=a'
    response = client.get(url)
    assert response.status_code == 200


def test_search_for_rooms_should_not_crash(client):
    url = reverse('room-search') + '?query=a'
    response = client.get(url)
    assert response.status_code == 200


def test_search_for_locations_should_not_crash(client):
    url = reverse('location-search') + '?query=a'
    response = client.get(url)
    assert response.status_code == 200


def test_search_for_vlans_should_not_crash(client):
    url = reverse('vlan-index') + '?query=a'
    response = client.get(url)
    assert response.status_code == 200


def test_search_for_prefixes_should_not_crash(client):
    url = reverse('prefix-index') + '?query=a'
    response = client.get(url)
    assert response.status_code == 200


def test_search_for_device_groups_should_not_crash(client):
    url = reverse('netbox-group') + '?query=a'
    response = client.get(url)
    assert response.status_code == 200


class TestIndexSearchPreviewView:
    """Tests for the search preview feature."""

    def test_given_empty_query_it_should_return_no_results(self, client):
        response = self._handle_search_request(client, '')
        assert response.status_code == 200
        assert response.context['results'] is None

    def test_given_empty_query_it_should_return_close_popover_event(self, client):
        response = self._handle_search_request(client, '')
        assert 'HX-Trigger' in response.headers
        assert 'popover.close' in response.headers['HX-Trigger']

    def test_given_existing_resource_it_should_return_results(self, client):
        response = self._handle_search_request(client, "myroom")
        assert response.status_code == 200
        assert len(response.context['results']) > 0

    def test_given_valid_query_it_should_return_results(self, client, db, localhost):
        response = self._handle_search_request(client, localhost.sysname)
        assert response.status_code == 200
        results = response.context['results']
        assert results is not None
        # At least one provider should have results
        assert any(len(provider.results) > 0 for provider in results)

    def test_given_more_than_five_results_then_it_should_truncate_results(
        self, client, db, localhost
    ):
        # Create more than 5 interfaces to trigger truncation
        for i in range(10):
            create_interface(localhost, ifname=f'GigabitEthernet0/{i}')
        response = self._handle_search_request(client, "Test Interface")
        results = response.context['results']
        # Find the Interfaces provider
        provider = next((p for p in results if p.name == 'Interfaces'), None)
        assert provider is not None
        assert provider.count == 10
        assert len(provider.results) == 5  # Should be truncated to 5
        assert provider.truncated is True
        assert provider.truncated_count == 5

    @staticmethod
    def _handle_search_request(client, query):
        url = reverse('info-search-preview') + f'?query={query}'
        return client.get(url)


def create_interface(
    netbox, ifname='GigabitEthernet0/1', ifalias='Test Interface', **kwargs
):
    """Create a test interface"""
    interface = Interface(netbox=netbox, ifname=ifname, ifalias=ifalias, **kwargs)
    interface.save()
    return interface
