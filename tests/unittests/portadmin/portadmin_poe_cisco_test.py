from mock import Mock

import pytest

from nav.portadmin.snmp.cisco import Cisco
from nav.portadmin.handlers import (
    POEIndexNotFoundError,
    POEStateNotSupportedError,
)
from nav.models import manage


def test_returns_correct_poe_state_options_cisco(handler_cisco):
    state_options = handler_cisco.get_poe_state_options()
    assert Cisco.POE_AUTO in state_options
    assert Cisco.POE_STATIC in state_options
    assert Cisco.POE_LIMIT in state_options
    assert Cisco.POE_DISABLE in state_options


class TestGetPoeState:
    def test_should_raise_exception_if_unknown_poe_state_cisco(self, handler_cisco):
        handler_cisco._get_poe_indexes_for_interface = Mock(return_value=(1, 1))
        handler_cisco._query_netbox = Mock(return_value=76)
        interface = Mock()
        with pytest.raises(POEStateNotSupportedError):
            handler_cisco.get_poe_states([interface])

    def test_should_raise_exception_if_no_poe_indexes_cisco(self, handler_cisco):
        handler_cisco._get_poe_indexes_for_interface = Mock(
            side_effect=POEIndexNotFoundError("Fail")
        )
        interface = Mock()
        with pytest.raises(POEIndexNotFoundError):
            handler_cisco.get_poe_states([interface])

    def test_dict_should_give_none_if_interface_does_not_support_poe(
        self, handler_cisco
    ):
        handler_cisco._get_poe_indexes_for_interface = Mock(return_value=(1, 1))
        handler_cisco._query_netbox = Mock(return_value=None)
        interface = Mock(interface="interface")
        states = handler_cisco.get_poe_states([interface])
        assert states[interface.ifname] is None

    def test_returns_correct_poe_state_cisco(self, handler_cisco):
        expected_state = Cisco.POE_AUTO
        handler_cisco._get_poe_indexes_for_interface = Mock(return_value=(1, 1))
        handler_cisco._query_netbox = Mock(return_value=expected_state.state)
        interface = Mock(ifname="interface")
        state = handler_cisco.get_poe_states([interface])
        assert state[interface.ifname] == expected_state

    def test_use_interfaces_from_db_if_empty_interfaces_arg(self, handler_cisco):
        expected_state = Cisco.POE_AUTO
        handler_cisco._get_poe_indexes_for_interface = Mock(return_value=(1, 1))
        handler_cisco._query_netbox = Mock(return_value=expected_state.state)
        interface = Mock(ifname="interface")
        handler_cisco.netbox.interfaces = [interface]
        state = handler_cisco.get_poe_states()
        assert interface.ifname in state


class TestGetPoeIndexesForInterface:
    def test_returns_correct_values(self, handler_cisco):
        poegroup_mock = Mock(index=1)
        poeport_mock = Mock(poegroup=poegroup_mock, index=2)
        handler_cisco._get_poeport = Mock(return_value=poeport_mock)
        interface = Mock(ifname="interface")
        unit_number, if_number = handler_cisco._get_poe_indexes_for_interface(interface)
        assert unit_number == poegroup_mock.index
        assert if_number == poeport_mock.index

    def test_raises_exception_if_no_poeport_exists(self, handler_cisco):
        handler_cisco._get_poeport = Mock(
            side_effect=manage.POEPort.DoesNotExist("Fail")
        )
        interface = Mock(ifname="interface")
        with pytest.raises(POEIndexNotFoundError):
            handler_cisco._get_poe_indexes_for_interface(interface)
