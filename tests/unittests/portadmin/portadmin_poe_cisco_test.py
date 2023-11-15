from mock import Mock, patch

import pytest

from nav.portadmin.snmp.cisco import Cisco
from nav.portadmin.handlers import (
    POEIndexNotFoundError,
    POEStateNotSupportedError,
)
from nav.models import manage


class TestGetPoeStateOptions:
    def test_returns_correct_options(self, handler_cisco):
        state_options = handler_cisco.get_poe_state_options()
        assert Cisco.POE_AUTO in state_options
        assert Cisco.POE_STATIC in state_options
        assert Cisco.POE_LIMIT in state_options
        assert Cisco.POE_DISABLE in state_options


class TestGetPoeState:
    @pytest.mark.usefixtures('poeport_get_mock')
    def test_should_raise_exception_if_unknown_poe_state(self, handler_cisco):
        handler_cisco._query_netbox = Mock(return_value=76)
        interface = Mock(interface="interface")
        with pytest.raises(POEStateNotSupportedError):
            handler_cisco.get_poe_states([interface])

    @pytest.mark.usefixtures('poeport_get_mock_error')
    def test_should_raise_exception_if_interface_is_missing_poeport(
        self, handler_cisco
    ):
        interface = Mock(interface="interface")
        with pytest.raises(POEIndexNotFoundError):
            handler_cisco.get_poe_states([interface])

    @pytest.mark.usefixtures('poeport_get_mock')
    def test_dict_should_give_none_if_interface_does_not_support_poe(
        self, handler_cisco
    ):
        handler_cisco._query_netbox = Mock(return_value=None)
        interface = Mock(interface="interface")
        states = handler_cisco.get_poe_states([interface])
        assert states[interface.ifname] is None

    @pytest.mark.usefixtures('poeport_get_mock')
    def test_returns_correct_poe_state(self, handler_cisco):
        expected_state = Cisco.POE_AUTO
        handler_cisco._query_netbox = Mock(return_value=expected_state.state)
        interface = Mock(ifname="interface")
        state = handler_cisco.get_poe_states([interface])
        assert state[interface.ifname] == expected_state

    @pytest.mark.usefixtures('poeport_get_mock')
    def test_use_interfaces_from_db_if_empty_interfaces_arg(self, handler_cisco):
        expected_state = Cisco.POE_AUTO
        handler_cisco._query_netbox = Mock(return_value=expected_state.state)
        interface = Mock(ifname="interface")
        handler_cisco.netbox.interfaces = [interface]
        state = handler_cisco.get_poe_states()
        assert interface.ifname in state


@pytest.fixture()
def poeport_get_mock():
    with patch("nav.portadmin.snmp.cisco.manage.POEPort.objects.get") as get_mock:
        poegroup_mock = Mock(index=1)
        poeport_mock = Mock(poegroup=poegroup_mock, index=1)
        get_mock.return_value = poeport_mock
        yield get_mock


@pytest.fixture()
def poeport_get_mock_error():
    with patch("nav.portadmin.snmp.cisco.manage.POEPort.objects.get") as get_mock:
        get_mock.side_effect = manage.POEPort.DoesNotExist
        yield get_mock
