import socket

import pytest
from django.http import HttpResponse
from django.urls import reverse
from django.utils.encoding import smart_str
from mock import Mock, patch

from nav.models.manage import ManagementProfile, NetboxType, Vendor
from nav.Snmp.errors import SnmpError
from nav.web.seeddb.page.netbox.edit import (
    get_snmp_read_only_variables,
    snmp_write_test,
)


class TestCheckConnectivityView:
    """
    Test cases for the check_connectivity view.

    This view validates IP addresses/hostnames and returns appropriate responses
    for use with HTMX frontend interactions.
    """

    url = reverse('seeddb-netbox-check-connectivity')

    @staticmethod
    def _get_post_data(ip_address: str = '', profiles=None):
        """Helper method to create consistent POST data for connectivity tests"""
        if profiles is None:
            profiles = [123]
        return {'ip': ip_address, 'profiles': profiles}

    def test_given_no_address_it_should_return_error_response(self, client):
        """Test that missing address parameter returns error response"""
        response = client.post(self.url)
        assert response.status_code == 200
        assert response.context['status'] == 'error'

    def test_given_empty_address_it_should_return_error_response(self, client):
        """Test that empty address parameter returns 400"""
        response = client.post(self.url, data=self._get_post_data(ip_address=''))
        assert response.status_code == 200
        assert response.context['status'] == 'error'

    def test_given_whitespace_only_ip_it_should_return_error_response(self, client):
        """Test that IP address with only whitespace returns error response"""
        response = client.post(self.url, data=self._get_post_data(ip_address='   '))
        assert response.status_code == 200
        assert response.context['status'] == 'error'

    def test_given_no_profiles_parameter_it_should_return_error_response(
        self, client, valid_ipv4
    ):
        """Test that missing profiles parameter returns error response"""
        response = client.post(self.url, {'ip': valid_ipv4})
        assert response.status_code == 200
        assert response.context['status'] == 'error'
        assert response.context['message']

    def test_given_empty_profiles_list_it_should_return_error_response(
        self, client, valid_ipv4
    ):
        """Test that empty profiles list returns error response"""
        response = client.post(self.url, {'ip': valid_ipv4, 'profiles': []})
        assert response.status_code == 200
        assert response.context['status'] == 'error'

    def test_given_valid_ipv4_address_it_should_return_loading_response(
        self, client, valid_ipv4
    ):
        """
        Test that a valid IP address returns a loading status.

        When a valid IP is provided, the view should return a loading status
        to indicate that connectivity tests can proceed.
        """
        response = client.post(
            self.url, data=self._get_post_data(ip_address=valid_ipv4)
        )
        assert response.status_code == 200
        assert response.context['status'] == 'loading'

    def test_given_valid_ipv6_address_it_should_return_loading_response(
        self, client, valid_ipv6
    ):
        """Test that valid IPv6 address returns loading status"""
        response = client.post(
            self.url, data=self._get_post_data(ip_address=valid_ipv6)
        )
        assert response.status_code == 200
        assert response.context['status'] == 'loading'

    def test_given_malformed_ip_address_it_should_attempt_hostname_resolution(
        self, client
    ):
        """Test that malformed IP is treated as hostname and resolved"""
        response = client.post(
            self.url, data=self._get_post_data(ip_address='999.999.999.999')
        )
        assert response.status_code == 200
        assert response.context['status'] == 'error'

    @patch('socket.getaddrinfo')
    def test_given_valid_hostname_then_return_sorted_ip_addresses(
        self, mock_getaddrinfo, client
    ):
        """Test that valid hostname returns associated IP addresses sorted"""
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('192.168.1.10', 0)),
            (2, 1, 6, '', ('192.168.1.5', 0)),
        ]
        response = client.post(
            self.url, data=self._get_post_data(ip_address='example.com')
        )
        assert response.status_code == 200
        assert response.context['status'] == 'select-address'
        assert response.context['addresses'] == ['192.168.1.5', '192.168.1.10']

    @patch('socket.getaddrinfo')
    def test_given_hostname_with_mixed_ipv4_ipv6_then_return_sorted_addresses(
        self, mock_getaddrinfo, client
    ):
        """
        Test that hostname resolving to both IPv4 and IPv6 returns sorted addresses
        """
        mock_getaddrinfo.return_value = [
            (socket.AF_INET6, 1, 6, '', ('2001:db8::2', 0, 0, 0)),
            (socket.AF_INET, 1, 6, '', ('192.168.1.10', 0)),
            (socket.AF_INET6, 1, 6, '', ('2001:db8::1', 0, 0, 0)),
            (socket.AF_INET, 1, 6, '', ('192.168.1.5', 0)),
        ]
        response = client.post(
            self.url, data=self._get_post_data(ip_address='example.com')
        )
        assert response.status_code == 200
        assert response.context['status'] == 'select-address'
        # Verify both IPv4 and IPv6 addresses are included and sorted as expected
        addresses = response.context['addresses']
        expected_order = ['2001:db8::1', '2001:db8::2', '192.168.1.5', '192.168.1.10']
        assert addresses == expected_order

    @patch('socket.getaddrinfo')
    def test_given_socket_error_then_return_error_message(
        self, mock_getaddrinfo, client
    ):
        """Test that socket error returns appropriate error message"""
        mock_getaddrinfo.side_effect = socket.error("Socket error")
        response = client.post(
            self.url, data=self._get_post_data(ip_address='example.com')
        )
        assert response.status_code == 200
        assert response.context['status'] == 'error'
        assert response.context['message'] == 'Socket error'

    def test_given_unknown_hostname_then_return_error_message(self, client):
        """Test that unknown host returns appropriate error message"""
        response = client.post(
            self.url, data=self._get_post_data(ip_address='unknown.host')
        )

        assert response.status_code == 200
        assert response.context['status'] == 'error'
        assert 'Name or service not known' in response.context['message']

    @patch('socket.getaddrinfo')
    def test_given_unicode_error_then_return_error_message(
        self, mock_getaddrinfo, client
    ):
        """Test that unicode error returns appropriate error message"""
        mock_getaddrinfo.side_effect = UnicodeError("Invalid Unicode characters")
        response = client.post(
            self.url, data=self._get_post_data(ip_address='test.example.com')
        )

        assert response.status_code == 200
        assert response.context['status'] == 'error'
        assert response.context['message'] == 'Invalid Unicode characters'


class TestLoadConnectivityTestResultsView:
    url = reverse('seeddb-netbox-check-connectivity-load')

    @staticmethod
    def _get_profile_from_response(
        response: HttpResponse, profile_id: int, key: str = "succeeded"
    ):
        profiles = response.context.get('profiles', {})  # Add .get() with default
        if key not in profiles:
            return None
        profile_list = profiles[key]
        return next((p for p in profile_list if p['id'] == profile_id), None)

    def test_given_no_profile_ids_then_return_not_found_response(
        self, client, valid_ipv4
    ):
        """Test that missing profiles returns not found response"""

        response = client.post(self.url, {'ip': valid_ipv4})
        assert response.status_code == 200
        assert response.context.get('profiles') is None
        assert "No profiles found" in smart_str(response.content)

    def test_given_non_existent_profiles_then_return_not_found_response(
        self, client, valid_ipv4
    ):
        """Test that invalid profile IDs returns not found response"""

        response = client.post(
            self.url, {'ip': valid_ipv4, 'profiles': ['9999', '8888']}
        )
        assert response.status_code == 200
        assert response.context.get('profiles') is None
        assert "No profiles found" in smart_str(response.content)

    @patch('nav.web.seeddb.page.netbox.edit.get_sysname')
    @patch('nav.web.seeddb.page.netbox.edit.get_snmp_read_only_variables')
    def test_given_snmp_profile_then_set_sysname_and_netbox_type_in_response(
        self,
        mock_snmp_vars,
        mock_sysname,
        client,
        snmp_profile,
        netbox_type,
        valid_ipv4,
    ):
        """Test that valid profile returns sysname and netbox_type"""
        mock_sysname.return_value = 'test-device.example.com'
        mock_snmp_vars.return_value = {'status': True, 'type': netbox_type}
        response = client.post(
            self.url,
            {'ip': valid_ipv4, 'profiles': [str(snmp_profile.id)]},
        )
        assert response.status_code == 200
        assert response.context['sysname'] == 'test-device.example.com'
        assert response.context['netbox_type'] == netbox_type

    @patch('nav.web.seeddb.page.netbox.edit.get_sysname')
    @patch('nav.web.seeddb.page.netbox.edit.get_snmp_read_only_variables')
    def test_given_snmp_profile_then_return_snmp_data(
        self,
        mock_snmp_vars,
        mock_sysname,
        client,
        snmp_profile,
        netbox_type,
        valid_ipv4,
    ):
        """Test that SNMP profile returns SNMP data"""
        mock_sysname.return_value = 'test-device.example.com'
        mock_snmp_vars.return_value = {'status': True, 'type': netbox_type}

        response = client.post(
            self.url,
            {'ip': valid_ipv4, 'profiles': [str(snmp_profile.id)]},
        )

        profile_data = self._get_profile_from_response(response, snmp_profile.id)

        assert response.status_code == 200
        assert profile_data and profile_data['status'] is True
        assert profile_data and profile_data['name'] == snmp_profile.name

    @patch('nav.web.seeddb.page.netbox.edit.get_sysname')
    @patch('nav.web.seeddb.page.netbox.edit.get_snmp_read_only_variables')
    def test_given_snmp_profile_with_failure_then_return_in_failed_section(
        self, mock_snmp_vars, mock_sysname, client, snmp_profile, valid_ipv4
    ):
        """Test that failed SNMP profile appears in failed section"""
        mock_sysname.return_value = 'test-device.example.com'
        mock_snmp_vars.return_value = {
            'status': False,
            'error_message': 'Connection timeout',
        }

        response = client.post(
            self.url, {'ip': valid_ipv4, 'profiles': [str(snmp_profile.id)]}
        )

        profile_data = self._get_profile_from_response(
            response, snmp_profile.id, key="failed"
        )
        assert profile_data is not None
        assert profile_data['status'] is False
        assert profile_data['error_message'] == 'Connection timeout'

    @patch('nav.web.seeddb.page.netbox.edit.get_sysname')
    @patch('nav.web.seeddb.page.netbox.edit.test_napalm_connectivity')
    def test_given_napalm_profile_then_return_napalm_data(
        self, mock_napalm, mock_sysname, client, napalm_profile, valid_ipv4
    ):
        """Test that NAPALM profile returns NAPALM connectivity data"""
        mock_sysname.return_value = 'test-device.example.com'
        mock_napalm.return_value = {'status': True}

        response = client.post(
            self.url,
            {'ip': valid_ipv4, 'profiles': [str(napalm_profile.id)]},
        )
        profile_data = self._get_profile_from_response(response, napalm_profile.id)

        assert response.status_code == 200
        assert profile_data['name'] == 'Test napalm profile'
        assert profile_data['status'] is True

    @patch('nav.web.seeddb.page.netbox.edit.get_sysname')
    @patch('nav.web.seeddb.page.netbox.edit.test_napalm_connectivity')
    def test_given_napalm_profile_with_exception_then_return_in_failed_section(
        self, mock_napalm, mock_sysname, client, napalm_profile, valid_ipv4
    ):
        """Test that NAPALM profile with connection error appears in failed section"""
        mock_sysname.return_value = 'test-device.example.com'
        mock_napalm.return_value = {
            'status': False,
            'error_message': 'Authentication failed',
        }

        response = client.post(
            self.url, {'ip': valid_ipv4, 'profiles': [str(napalm_profile.id)]}
        )

        profile_data = self._get_profile_from_response(
            response, napalm_profile.id, key="failed"
        )
        assert profile_data is not None
        assert profile_data['status'] is False

    @patch('nav.web.seeddb.page.netbox.edit.get_sysname')
    def test_given_unhandled_profile_then_include_profile_in_failed_response(
        self, mock_sysname, client, unhandled_profile, valid_ipv4
    ):
        """Test that unsupported profile appears in failed section"""
        mock_sysname.return_value = 'test-device.example.com'
        response = client.post(
            self.url,
            {'ip': valid_ipv4, 'profiles': [str(unhandled_profile.id)]},
        )
        profile_data = self._get_profile_from_response(
            response, unhandled_profile.id, key="failed"
        )

        assert response.status_code == 200
        assert response.context['netbox_type'] is None
        assert profile_data['name'] == unhandled_profile.name
        assert profile_data['status'] is False

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
        netbox_type,
        valid_ipv4,
    ):
        """Test that multiple profiles return data for each"""
        mock_sysname.return_value = 'multi-device.example.com'
        mock_snmp_vars.return_value = {'status': True, 'type': netbox_type}
        mock_napalm.return_value = {
            'status': True,
        }

        response = client.post(
            self.url,
            {
                'ip': valid_ipv4,
                'profiles': [str(snmp_profile.id), str(napalm_profile.id)],
            },
        )

        snmp_check = self._get_profile_from_response(response, snmp_profile.id)
        napalm_check = self._get_profile_from_response(response, napalm_profile.id)
        assert response.status_code == 200
        assert snmp_check is not None
        assert napalm_check is not None


class TestValidateIpAddressView:
    def test_given_valid_ipv4_it_should_return_200(self, client, valid_ipv4):
        """Test that valid IPv4 address returns 200 response"""
        url = reverse('seeddb-netbox-validate-ip-address')
        response = client.get(url, {'address': valid_ipv4})
        assert response.status_code == 200

    def test_given_valid_ipv6_it_should_return_200(self, client, valid_ipv6):
        """Test that valid IPv6 address returns 200 response"""
        url = reverse('seeddb-netbox-validate-ip-address')
        response = client.get(url, {'address': valid_ipv6})
        assert response.status_code == 200

    def test_given_invalid_address_it_should_return_400(self, client):
        """Test that invalid address returns 400 response"""
        url = reverse('seeddb-netbox-validate-ip-address')
        response = client.get(url, {'address': 'invalid_address'})
        assert response.status_code == 400


class TestGetSnmpReadOnlyVariables:
    """Test cases for get_snmp_read_only_variables function"""

    @patch('nav.web.seeddb.page.netbox.edit.snmp_write_test')
    def test_given_write_profile_then_call_write_test(
        self, mock_write_test, snmp_write_profile, valid_ipv4
    ):
        """Test that write profiles trigger write test"""
        mock_write_test.return_value = {'status': True, 'syslocation': 'test'}

        result = get_snmp_read_only_variables(valid_ipv4, snmp_write_profile)

        mock_write_test.assert_called_once_with(valid_ipv4, snmp_write_profile)
        assert result == {'status': True, 'syslocation': 'test'}

    @patch('nav.web.seeddb.page.netbox.edit.check_snmp_version')
    @patch('nav.web.seeddb.page.netbox.edit.get_netbox_type')
    def test_given_read_profile_success_then_return_type_and_status(
        self, mock_get_type, mock_check_version, snmp_profile, netbox_type, valid_ipv4
    ):
        """Test successful read-only profile returns type and status"""
        mock_get_type.return_value = netbox_type
        mock_check_version.return_value = True

        result = get_snmp_read_only_variables(valid_ipv4, snmp_profile)

        assert result['type'] == netbox_type
        assert result['status'] is True
        assert 'error_message' not in result

    @patch('nav.web.seeddb.page.netbox.edit.check_snmp_version')
    @patch('nav.web.seeddb.page.netbox.edit.get_netbox_type')
    def test_given_read_profile_failure_then_return_error_message(
        self, mock_get_type, mock_check_version, snmp_profile, netbox_type, valid_ipv4
    ):
        """Test failed read-only profile returns error message"""
        mock_get_type.return_value = netbox_type
        mock_check_version.return_value = False

        result = get_snmp_read_only_variables(valid_ipv4, snmp_profile)

        assert result['type'] == netbox_type
        assert result['status'] is False
        assert result['error_message'] == "SNMP connection failed"


class TestSnmpWriteTest:
    """Test cases for snmp_write_test function"""

    @patch('nav.web.seeddb.page.netbox.edit.get_snmp_session_for_profile')
    def test_given_successful_write_then_return_success_status(
        self, mock_session_factory, snmp_write_profile, valid_ipv4
    ):
        """Test successful SNMP write operation"""
        mock_snmp = Mock()
        mock_snmp.get.return_value = 'Test Location'
        mock_snmp.set.return_value = None
        mock_session_factory.return_value = Mock(return_value=mock_snmp)

        result = snmp_write_test(valid_ipv4, snmp_write_profile)

        assert result['status'] is True
        assert result['syslocation'] == 'Test Location'
        assert result['error_message'] == ''
        mock_snmp.get.assert_called_once_with('1.3.6.1.2.1.1.6.0')
        mock_snmp.set.assert_called_once_with(
            '1.3.6.1.2.1.1.6.0', 's', b'Test Location'
        )

    @patch('nav.web.seeddb.page.netbox.edit.get_snmp_session_for_profile')
    def test_given_snmp_error_then_return_failure_status(
        self, mock_session_factory, snmp_write_profile, valid_ipv4
    ):
        """Test SNMP error during write operation"""
        mock_snmp = Mock()
        mock_snmp.get.side_effect = SnmpError("Authentication failed")
        mock_session_factory.return_value = Mock(return_value=mock_snmp)

        result = snmp_write_test(valid_ipv4, snmp_write_profile)

        assert result['status'] is False
        assert result['error_message'] == 'Authentication failed'
        assert result['syslocation'] == ''

    @patch('nav.web.seeddb.page.netbox.edit.get_snmp_session_for_profile')
    def test_given_unicode_error_then_return_custom_error(
        self, mock_session_factory, snmp_write_profile, valid_ipv4
    ):
        """Test Unicode decode error during write operation"""
        mock_snmp = Mock()
        mock_snmp.get.return_value = b'\x80'
        mock_snmp.set.side_effect = UnicodeDecodeError(
            'utf-8', b'\x80', 0, 1, 'invalid start byte'
        )
        mock_session_factory.return_value = Mock(return_value=mock_snmp)

        result = snmp_write_test(valid_ipv4, snmp_write_profile)

        assert result['status'] is False
        assert result['custom_error'] == 'UnicodeDecodeError'
        assert result['error_message'] == "Could not decode SNMP response"


@pytest.fixture()
def netbox_type():
    vendor = Vendor(id="TestVendor")
    vendor.save()
    netbox_type = NetboxType(
        id=123,
        vendor=vendor,
        name="TEST-12A-BC-3",
        description="Test Device Type",
    )
    netbox_type.save()
    yield netbox_type
    netbox_type.delete()
    vendor.delete()


@pytest.fixture
def valid_ipv4():
    return '192.168.1.1'


@pytest.fixture
def valid_ipv6():
    return '2001:db8::1'


@pytest.fixture
def invalid_hostname():
    return 'nonexistent.invalid.domain'


@pytest.fixture()
def snmp_profile():
    yield from create_profile("Test SNMP profile", ManagementProfile.PROTOCOL_SNMP)


@pytest.fixture()
def snmp_write_profile():
    """Create an SNMP profile with write access"""
    yield from create_profile(
        "Test SNMP write profile", ManagementProfile.PROTOCOL_SNMP, write=True
    )


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
