# -*- coding: utf-8 -*-
import pytest
from django.db import models
from django.urls import reverse

from nav.models.manage import Interface, Location, NetType, Room, Vlan, NetboxGroup
from nav.web.info.forms import SearchForm
from nav.web.info.views import process_form


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


class TestProcessFormDescriptionSearch:
    """Tests for process_form view searching by description."""

    def test_location_search_by_description_should_return_results(self, db):
        location = Location.objects.create(
            id="testlocation", description="test location description"
        )

        self.assert_search_provider_result(
            instance=location,
            provider_name='Locations',
        )

    def test_room_search_by_description_should_return_results(self, db):
        room = Room.objects.create(
            id="testroom", description="test room description", location_id="mylocation"
        )

        self.assert_search_provider_result(
            instance=room,
            provider_name='Rooms',
        )

    def test_vlan_search_by_description_should_return_results(self, db):
        nettype = NetType.objects.create(description="testdescription")
        vlan = Vlan.objects.create(
            vlan="20", description="test vlan description", net_type=nettype
        )
        self.assert_search_provider_result(
            instance=vlan,
            provider_name='Vlans',
        )

    def test_devicegroup_search_by_description_should_return_results(
        self, db, localhost
    ):
        device_group = NetboxGroup.objects.create(
            id='test-group-001', description='Core network switches group'
        )
        self.assert_search_provider_result(
            instance=device_group,
            provider_name='Device groups',
        )

    @staticmethod
    def assert_search_provider_result(instance: models.Model, provider_name: str):
        """
        Helper method to assert that a search by description returns
        the expected instance.
        """

        form = SearchForm({'query': instance.description}, auto_id=False)
        form.is_valid()
        providers, _ = process_form(form)

        provider = next((p for p in providers if p.name == provider_name), None)
        assert provider is not None
        assert len(provider.results) == 1
        assert provider.results[0].inst.id == instance.id


class TestInfoSearchViews:
    """Tests for the info search views."""

    def test_info_search_general_query_should_return_base_template(self, client):
        """Should render base template for general query."""
        url = reverse('info-search') + '?query=a'
        response = client.get(url)
        assert response.status_code == 200
        assert 'info/base.html' in [t.name for t in response.templates]

    def test_info_search_query_matching_single_resource_should_redirect(
        self, client, localhost
    ):
        """Should redirect when query matches a single resource."""
        url = reverse('info-search') + f'?query={localhost.sysname}'
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == reverse(
            'ipdevinfo-details-by-name', kwargs={'name': localhost.sysname}
        )

    def test_info_search_general_query_using_htmx_should_return_search_results(
        self, client
    ):
        """Should return search results partial for HTMX request."""
        url = reverse('info-search') + '?query=a'
        response = client.get(url, HTTP_HX_REQUEST='true')
        assert response.status_code == 200
        assert 'info/_search_results.html' in [t.name for t in response.templates]

    def test_info_search_query_matching_single_resource_using_htmx_should_redirect(
        self, client, localhost
    ):
        """
        Should return HX-Redirect header for HTMX request matching single resource.
        """
        url = reverse('info-search') + f'?query={localhost.sysname}'
        response = client.get(url, HTTP_HX_REQUEST='true')
        assert response.status_code == 200
        assert 'HX-Redirect' in response.headers

    def test_ipdevinfo_search_query_that_matches_single_netbox_should_redirect(
        self, client, localhost
    ):
        """Should redirect for ipdevinfo search matching single netbox."""
        url = reverse('ipdevinfo-search') + f'?query={localhost.sysname}'
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == reverse(
            'ipdevinfo-details-by-name', kwargs={'name': localhost.sysname}
        )

    def test_ipdevinfo_single_netbox_query_should_redirect_with_htmx(
        self, client, localhost
    ):
        """
        Should return HX-Redirect for HTMX ipdevinfo search matching single netbox.
        """
        url = reverse('ipdevinfo-search') + f'?query={localhost.sysname}'
        response = client.get(url, HTTP_HX_REQUEST='true')
        assert response.status_code == 200
        assert 'HX-Redirect' in response.headers

    @pytest.mark.parametrize(
        'url_name,template',
        [
            ('ipdevinfo-search', 'info/base.html'),
            ('room-search', 'info/room/base.html'),
            ('location-search', 'info/location/base.html'),
            ('vlan-index', 'info/vlan/base.html'),
            ('prefix-index', 'info/prefix/base.html'),
            ('netbox-group', 'info/netboxgroup/list_groups.html'),
        ],
    )
    def test_search_views_should_render_base_template_on_initial_load(
        self, client, url_name, template
    ):
        """Should render correct base template for each search view."""
        url = reverse(url_name) + '?query=unmatched'
        response = client.get(url)
        assert response.status_code == 200
        assert template in [t.name for t in response.templates]

    @pytest.mark.parametrize(
        'url_name,template',
        [
            ('ipdevinfo-search', 'ipdevinfo/_search_results.html'),
            ('room-search', 'info/room/_search_results.html'),
            ('location-search', 'info/location/_search_results.html'),
            ('vlan-index', 'info/vlan/_search_results.html'),
            ('prefix-index', 'info/prefix/_search_results.html'),
            ('netbox-group', 'info/netboxgroup/_search_results.html'),
        ],
    )
    def test_search_views_should_render_results_with_htmx(
        self, client, url_name, template
    ):
        url = reverse(url_name) + '?query=unmatched'
        response = client.get(url, HTTP_HX_REQUEST='true')
        assert response.status_code == 200
        assert template in [t.name for t in response.templates]


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
