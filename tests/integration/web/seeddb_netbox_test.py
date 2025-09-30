import socket

import pytest
from django.urls import reverse
from mock import patch

from nav.models.manage import ManagementProfile


class TestGetAddressInfo:
    url = reverse('seeddb-netbox-get-address-info')

    def test_given_no_address_it_should_return_400(self, client):
        """Test that missing address parameter returns 400"""
        response = client.get(self.url)
        assert response.status_code == 400
        assert response.content == b'No address given'

    def test_given_empty_address_it_should_return_400(self, client):
        """Test that empty address parameter returns 400"""
        response = client.get(self.url, {'address': ''})
        assert response.status_code == 400
        assert response.content == b'No address given'

    def test_given_valid_ip_address_it_should_return_is_ip_true(self, client):
        """Test that valid IP address returns is_ip: True"""
        response = client.get(self.url, {'address': '192.168.1.1'})
        assert response.status_code == 200
        assert response.json()['is_ip'] is True

    @patch('socket.getaddrinfo')
    def test_given_valid_hostname_then_return_sorted_ip_addresses(
        self, mock_getaddrinfo, client
    ):
        """Test that valid hostname returns associated IP addresses sorted"""
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('192.168.1.10', 0)),
            (2, 1, 6, '', ('192.168.1.5', 0)),
        ]
        response = client.get(self.url, {'address': 'example.com'})
        json_data = response.json()

        assert response.status_code == 200
        assert json_data['addresses'] == ['192.168.1.5', '192.168.1.10']

    @patch('socket.getaddrinfo')
    def test_given_socket_error_then_return_error_message(
        self, mock_getaddrinfo, client
    ):
        """Test that socket error returns appropriate error message"""
        mock_getaddrinfo.side_effect = socket.error("Socket error")
        response = client.get(self.url, {'address': 'example.com'})
        assert response.status_code == 200
        assert response.json()['error'] == 'Socket error'

    def test_given_unknown_hostname_then_return_error_message(self, client):
        """Test that unknown host returns appropriate error message"""
        response = client.get(self.url, {'address': 'unknown.host'})

        assert response.status_code == 200
        error_message = response.json()['error']
        assert 'Name or service not known' in error_message

    @patch('socket.getaddrinfo')
    def test_given_unicode_error_then_return_error_message(
        self, mock_getaddrinfo, client
    ):
        """Test that unicode error returns appropriate error message"""
        mock_getaddrinfo.side_effect = UnicodeError("Invalid Unicode characters")
        response = client.get(self.url, {'address': 'test.example.com'})

        assert response.status_code == 200
        assert response.json()['error'] == 'Invalid Unicode characters'


class TestGetReadOnlyVariablesView:
    url = reverse('seeddb-netbox-get-readonly')

    def test_given_no_profiles_then_return_404(self, client):
        """Test that missing profiles returns 404 response"""

        response = client.get(self.url, {'ip_address': '192.168.1.1'})
        assert response.status_code == 404

    def test_given_invalid_profile_ids_then_return_404(self, client):
        """Test that invalid profile IDs returns 404 response"""

        response = client.get(
            self.url, {'ip_address': '192.168.1.1', 'profile_ids': ['9999', '8888']}
        )
        assert response.status_code == 404

    @patch('nav.web.seeddb.page.netbox.edit.get_sysname')
    @patch('nav.web.seeddb.page.netbox.edit.get_snmp_read_only_variables')
    def test_given_snpm_profile_then_set_sysname_and_netbox_type_in_response(
        self, mock_snmp_vars, mock_sysname, client, snmp_profile
    ):
        """Test that valid profile returns sysname and netbox_type"""
        mock_sysname.return_value = 'test-device.example.com'
        mock_snmp_vars.return_value = {'status': True, 'type': 123}
        response = client.get(
            self.url,
            {'ip_address': '192.168.1.1', 'profiles[]': [str(snmp_profile.id)]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data['sysname'] == 'test-device.example.com'
        assert data['netbox_type'] == 123

    @patch('nav.web.seeddb.page.netbox.edit.get_sysname')
    @patch('nav.web.seeddb.page.netbox.edit.get_snmp_read_only_variables')
    def test_given_snmp_profile_then_return_snmp_data(
        self, mock_snmp_vars, mock_sysname, client, snmp_profile
    ):
        """Test that SNMP profile returns SNMP data"""
        mock_sysname.return_value = 'test-device.example.com'
        mock_snmp_vars.return_value = {'status': True, 'type': 123}

        response = client.get(
            self.url,
            {'ip_address': '192.168.1.1', 'profiles[]': [str(snmp_profile.id)]},
        )

        json_data = response.json()
        profile_data = json_data['profiles'][str(snmp_profile.id)]

        assert response.status_code == 200
        assert profile_data['status'] is True
        assert profile_data['name'] == snmp_profile.name

    @patch('nav.web.seeddb.page.netbox.edit.get_sysname')
    @patch('nav.web.seeddb.page.netbox.edit.test_napalm_connectivity')
    def test_given_napalm_profile_then_return_napalm_data(
        self, mock_napalm, mock_sysname, client, napalm_profile
    ):
        """Test that NAPALM profile returns NAPALM connectivity data"""
        mock_sysname.return_value = 'test-device.example.com'
        mock_napalm.return_value = {'status': True}

        response = client.get(
            self.url,
            {'ip_address': '192.168.1.2', 'profiles[]': [str(napalm_profile.id)]},
        )

        data = response.json()
        profile_data = data['profiles'][str(napalm_profile.id)]

        assert response.status_code == 200
        assert profile_data['name'] == 'Test napalm profile'
        assert profile_data['status'] is True

    @patch('nav.web.seeddb.page.netbox.edit.get_sysname')
    def test_given_unhandled_profile_then_return_none_data(
        self, mock_sysname, client, unhandled_profile
    ):
        """Test that unhandled profile type returns None data"""
        mock_sysname.return_value = 'test-device.example.com'
        response = client.get(
            self.url,
            {'ip_address': '192.168.1.1', 'profiles[]': [str(unhandled_profile.id)]},
        )
        data = response.json()
        assert response.status_code == 200
        assert data['netbox_type'] is None
        assert data['profiles'][str(unhandled_profile.id)] == {}

    @patch('nav.web.seeddb.page.netbox.edit.get_sysname')
    @patch('nav.web.seeddb.page.netbox.edit.get_snmp_read_only_variables')
    @patch('nav.web.seeddb.page.netbox.edit.test_napalm_connectivity')
    def test_given_multiple_profiles_then_return_all_profiles(
        self,
        mock_napalm,
        mock_snmp_vars,
        mock_sysname,
        client,
        snmp_profile,
        napalm_profile,
    ):
        """Test that multiple profiles return data for each"""
        mock_sysname.return_value = 'multi-device.example.com'
        mock_snmp_vars.return_value = {'status': True, 'type': 456}
        mock_napalm.return_value = {
            'status': False,
            'error_message': 'Connection failed',
        }

        response = client.get(
            self.url,
            {
                'ip_address': '192.168.1.4',
                'profiles[]': [str(snmp_profile.id), str(napalm_profile.id)],
            },
        )

        data = response.json()
        assert response.status_code == 200
        assert str(snmp_profile.id) in data['profiles']
        assert str(napalm_profile.id) in data['profiles']


@pytest.fixture()
def snmp_profile():
    yield from create_profile("Test SNMP profile", ManagementProfile.PROTOCOL_SNMP)


@pytest.fixture()
def napalm_profile():
    yield from create_profile("Test napalm profile", ManagementProfile.PROTOCOL_NAPALM)


@pytest.fixture()
def unhandled_profile():
    yield from create_profile("Unsupported profile", 99)


# This configuration dict is only relevant for SNMP profiles.
# For NAPALM and unsupported profiles, it is dummy data and not used,
# since all external interactions are mocked in tests.
def create_profile(name: str, protocol: int, write=False):
    profile = ManagementProfile(
        name=name,
        protocol=protocol,
        configuration={
            "version": 2,
            "community": "public",
            "write": write,
        },
    )
    profile.save()
    yield profile
    profile.delete()
