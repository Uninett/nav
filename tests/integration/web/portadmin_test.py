import uuid

import pytest
from django.http import HttpResponse
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils.encoding import smart_str
from jnpr.junos.exception import ConnectRefusedError
from mock import patch, Mock

from nav.models.manage import Interface, Netbox, NetboxProfile
from nav.portadmin.handlers import ManagementHandler
from nav.web.portadmin.views import populate_infodict, load_portadmin_data_by_kwargs


class TestFeedbackModal:
    def test_should_render_feedback_modal(self, client):
        url = reverse('portadmin-feedback-modal')
        response = client.get(url)
        assert 'id="portadmin-feedback-modal"' in smart_str(response.content)


class TestPortadminSearchViews:
    """Combined tests for all search view types"""

    @pytest.mark.parametrize(
        "url_name,fixture_name,attr_name,expected_status",
        [
            ("portadmin-interface", "interface", "id", 200),
            ("portadmin-sysname", "valid_netbox", "sysname", 200),
            ("portadmin-ip", "valid_netbox", "ip", 200),
        ],
    )
    def test_when_resource_exists_it_should_return_200(
        self, client, request, url_name, fixture_name, attr_name, expected_status
    ):
        fixture = request.getfixturevalue(fixture_name)
        value = getattr(fixture, attr_name)

        url = reverse(url_name, args=[value])
        response = client.get(url)
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "url_name,arg,expected_error",
        [
            ("portadmin-interface", 9999, "Could not find interface"),
            ("portadmin-sysname", "nonexistent", "Could not find IP device"),
            ("portadmin-ip", "123.5.6.12", "Could not find IP device"),
        ],
    )
    def test_when_resource_does_not_exist_it_should_return_error(
        self, client, url_name, arg, expected_error
    ):
        url = reverse(url_name, args=[arg])
        response = client.get(url)
        assert expected_error in smart_str(response.content)

    @pytest.mark.parametrize(
        "url_name,fixture_name,attr_name",
        [
            ("portadmin-interface", "interface", "id"),
            ("portadmin-sysname", "valid_netbox", "sysname"),
            ("portadmin-ip", "valid_netbox", "ip"),
        ],
    )
    def test_when_resource_exists_it_should_return_correct_data_url(
        self, client, request, url_name, fixture_name, attr_name
    ):
        fixture = request.getfixturevalue(fixture_name)
        value = getattr(fixture, attr_name)

        url = reverse(url_name, args=[value])
        response = client.get(url)
        expected_url = reverse(url_name + '-data', args=[value])

        assert response.status_code == 200
        assert f'hx-get="{expected_url}"' in smart_str(response.content)

    @pytest.mark.parametrize(
        "url_name,fixture_name,attr_name,expected_error",
        [
            (
                "portadmin-sysname",
                "netbox_without_type",
                "sysname",
                "IP device found but has no type",
            ),
            (
                "portadmin-ip",
                "netbox_without_type",
                "ip",
                "IP device found but has no type",
            ),
            (
                "portadmin-sysname",
                "netbox_without_ports",
                "sysname",
                "IP device has no ports",
            ),
            (
                "portadmin-ip",
                "netbox_without_ports",
                "ip",
                "IP device has no ports",
            ),
        ],
    )
    def test_when_netbox_preconditions_are_not_met_then_response_should_contain_expected_error_message(  # noqa: E501
        self, client, request, url_name, fixture_name, attr_name, expected_error
    ):
        fixture = request.getfixturevalue(fixture_name)
        value = getattr(fixture, attr_name)

        url = reverse(url_name, args=[value])
        response = client.get(url)
        assert expected_error in smart_str(response.content)


class TestPortadminDataLoading:
    """Tests for load_portadmin_data_by_kwargs and populate_infodict functions"""

    @patch('nav.web.portadmin.views.get_and_populate_livedata')
    @patch('nav.web.portadmin.views.render')
    def test_load_portadmin_data_by_kwargs_should_load_data_for_valid_interface_id(
        self, mock_render, mock_get_livedata, mock_request, interface, mock_handler
    ):
        """Test loading data by interface ID"""
        mock_get_livedata.return_value = mock_handler
        mock_render.return_value = HttpResponse('rendered')

        load_portadmin_data_by_kwargs(mock_request, interfaceid=interface.id)

        mock_get_livedata.assert_called_once_with(interface.netbox, [interface])
        mock_render.assert_called_once()
        assert mock_render.call_args[0][0] == mock_request
        assert mock_render.call_args[0][1] == 'portadmin/portlist.html'

    @patch('nav.web.portadmin.views.get_and_populate_livedata')
    @patch('nav.web.portadmin.views.render')
    def test_load_portadmin_data_by_kwargs_should_load_data_for_valid_sysname(
        self,
        mock_render,
        mock_get_livedata,
        mock_request,
        valid_netbox,
        mock_handler,
    ):
        """Test loading data by sysname"""
        mock_get_livedata.return_value = mock_handler
        mock_render.return_value = HttpResponse('rendered')

        load_portadmin_data_by_kwargs(mock_request, sysname=valid_netbox.sysname)

        interfaces = valid_netbox.get_swports_sorted()
        mock_get_livedata.assert_called_once_with(valid_netbox, interfaces)

    def test_load_portadmin_data_by_kwargs_should_return_error_when_interface_not_found(
        self, mock_request
    ):
        """Test handling of non-existent interface"""
        response = load_portadmin_data_by_kwargs(mock_request, interfaceid=9999)

        assert isinstance(response, HttpResponse)
        assert b'Interface not found' in response.content

    def test_load_portadmin_data_by_kwargs_should_return_error_when_netbox_not_found(
        self, mock_request
    ):
        """Test handling of non-existent netbox"""
        response = load_portadmin_data_by_kwargs(mock_request, sysname='nonexistent')

        assert isinstance(response, HttpResponse)
        assert b'IP device not found' in response.content

    def test_load_portadmin_data_by_kwargs_should_return_error_when_no_interfaces_exist(
        self, mock_request, valid_netbox
    ):
        """Test handling of netbox with no interfaces"""
        valid_netbox.interfaces.all().delete()

        response = load_portadmin_data_by_kwargs(
            mock_request, sysname=valid_netbox.sysname
        )

        assert isinstance(response, HttpResponse)
        assert b'No interfaces found' in response.content

    @patch('nav.web.portadmin.views.get_and_populate_livedata')
    def test_populate_infodict_should_set_readonly_mode_when_handler_not_configurable(
        self, mock_get_livedata, mock_request, interface, mock_handler
    ):
        """Test populate_infodict in readonly mode"""
        mock_handler.is_configurable.return_value = False
        mock_get_livedata.return_value = mock_handler

        netbox = interface.netbox
        interfaces = [interface]
        result = populate_infodict(mock_request, netbox, interfaces)

        mock_get_livedata.assert_called_once_with(netbox, interfaces)
        assert result['readonly'] is True
        assert result['netbox'] == netbox
        assert result['interfaces'] == interfaces
        assert result['handlertype'] == 'MockHandler'

    @patch('nav.web.portadmin.views.get_and_populate_livedata')
    @patch('nav.web.portadmin.views.find_and_populate_allowed_vlans')
    @patch('nav.web.portadmin.views._setup_voice_vlan')
    @patch('nav.web.portadmin.views._setup_poe_if_supported')
    @patch('nav.web.portadmin.views._setup_dot1x_if_enabled')
    @patch('nav.web.portadmin.views.mark_detained_interfaces')
    def test_populate_infodict_should_configure_all_features_when_handler_is_configurable(  # noqa: E501
        self,
        mock_mark_detained,
        mock_setup_dot1x,
        mock_setup_poe,
        mock_setup_voice,
        mock_find_vlans,
        mock_get_livedata,
        mock_request,
        interface,
        mock_handler,
    ):
        """Test populate_infodict in configurable mode"""
        mock_handler.is_configurable.return_value = True
        mock_get_livedata.return_value = mock_handler
        mock_find_vlans.return_value = []
        mock_setup_voice.return_value = None
        mock_setup_poe.return_value = (True, ['auto', 'on', 'off'])

        netbox = interface.netbox
        interfaces = [interface]
        result = populate_infodict(mock_request, netbox, interfaces)

        mock_find_vlans.assert_called_once_with(
            mock_request.account, netbox, interfaces, mock_handler
        )
        mock_setup_voice.assert_called_once_with(
            mock_request, netbox, interfaces, mock_handler
        )
        mock_mark_detained.assert_called_once_with(interfaces)
        mock_setup_dot1x.assert_called_once_with(interfaces, mock_handler)
        mock_setup_poe.assert_called_once_with(interfaces, mock_handler)

        assert result['readonly'] is False
        assert result['supports_poe'] is True
        assert result['poe_options'] == ['auto', 'on', 'off']

    @patch('nav.web.portadmin.views.messages')
    @patch('nav.web.portadmin.views.get_and_populate_livedata')
    def test_populate_infodict_should_set_readonly_mode_when_handler_raises_exception(
        self, mock_get_livedata, mock_messages, mock_request, interface
    ):
        """Test populate_infodict when handler raises exception"""
        from nav.portadmin.handlers import NoResponseError

        mock_get_livedata.side_effect = NoResponseError("Device not responding")

        netbox = interface.netbox
        interfaces = [interface]
        result = populate_infodict(mock_request, netbox, interfaces)

        # Should be readonly when handler fails
        assert result['readonly'] is True
        assert result['handlertype'] == 'NoneType'

        # Verify error message was added
        mock_messages.error.assert_called_once()

    @pytest.mark.parametrize(
        "exception,expected_msg",
        [
            (ConnectRefusedError("refused"), "Connection refused when contacting"),
            (Exception("generic error"), "Unknown error when contacting"),
        ],
    )
    @patch("nav.web.portadmin.views.get_and_populate_livedata")
    @patch("nav.web.portadmin.views.messages")
    def test_populate_infodict_should_handle_livedata_exceptions_and_add_error_message(
        self,
        mock_messages,
        mock_get_livedata,
        mock_request,
        interface,
        exception,
        expected_msg,
    ):
        mock_get_livedata.side_effect = exception
        netbox = interface.netbox
        interfaces = [interface]
        result = populate_infodict(mock_request, netbox, interfaces)

        assert result["readonly"] is True
        assert expected_msg in mock_messages.error.call_args[0][1]

    @patch('nav.web.portadmin.views.get_and_populate_livedata')
    @patch('nav.web.portadmin.views.json')
    def test_populate_infodict_should_format_auditlog_parameters_correctly(
        self, mock_json, mock_get_livedata, mock_request, interface, mock_handler
    ):
        """Test that auditlog parameters are correctly formatted"""
        mock_handler.is_configurable.return_value = True
        mock_get_livedata.return_value = mock_handler
        mock_json.dumps.return_value = '{"test": "json"}'

        interfaces = [interface]
        result = populate_infodict(mock_request, interface.netbox, interfaces)

        expected_params = {
            'object_model': 'interface',
            'object_pks': str(interface.pk),
            'subsystem': 'portadmin',
        }
        mock_json.dumps.assert_called_once_with(expected_params)
        assert result['auditlog_api_parameters'] == '{"test": "json"}'


@pytest.fixture
def mock_request(admin_account):
    factory = RequestFactory()
    request = factory.get('/')
    request.account = admin_account
    return request


@pytest.fixture
def mock_handler():
    handler = Mock(spec=ManagementHandler)
    handler.is_configurable.return_value = True
    handler.__class__.__name__ = 'MockHandler'
    # Mock the get_interfaces method to return interface data
    handler.get_interfaces.return_value = [
        {
            'name': 'GigabitEthernet0/1',
            'description': 'Test interface',
            'vlan': 100,
            'admin': 1,
            'oper': 1,
        }
    ]
    handler.get_netbox_vlans.return_value = []
    handler.get_netbox_vlan_tags.return_value = []
    handler.get_poe_state_options.return_value = []
    handler.get_poe_states.return_value = {}
    handler.is_port_access_control_enabled.return_value = False
    return handler


@pytest.fixture
def valid_netbox(db, management_profile, netbox_type):
    box = create_netbox_with_profile(management_profile, type=netbox_type)
    new_interface = create_interface(box)
    yield box
    new_interface.delete()
    box.delete()


@pytest.fixture
def interface(db, management_profile, netbox_type):
    netbox = create_netbox_with_profile(management_profile, type=netbox_type)
    interface = create_interface(netbox)
    interface.save()
    yield interface
    interface.delete()
    netbox.delete()


@pytest.fixture
def netbox_without_type(db, management_profile):
    box = create_netbox_with_profile(management_profile)
    new_interface = create_interface(box)
    yield box
    new_interface.delete()
    box.delete()


@pytest.fixture
def netbox_without_ports(db, management_profile, netbox_type):
    box = create_netbox_with_profile(management_profile, type=netbox_type)
    yield box
    box.delete()


def create_netbox_with_profile(management_profile, **kwargs):
    # Generate unique IP to avoid constraint violations
    unique_id = uuid.uuid4().int % 1000000
    ip = f'192.168.{(unique_id // 1000) % 256}.{unique_id % 256}'

    box = Netbox(
        ip=ip,
        sysname='test.example.org',
        organization_id='myorg',
        room_id='myroom',
        category_id='SRV',
        **kwargs,
    )
    box.save()
    NetboxProfile(netbox=box, profile=management_profile).save()
    return box


def create_interface(netbox, **kwargs):
    interface = Interface(
        netbox=netbox,
        ifname='GigabitEthernet0/1',
        ifalias='Test Interface',
        ifindex=1,
        iftype=6,
        baseport=1,
        **kwargs,
    )
    interface.save()
    return interface
