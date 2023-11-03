from mock import Mock

import pytest

from nav.portadmin.snmp.cisco import Cisco
from nav.portadmin.handlers import (
    POEIndexNotFoundError,
    POEStateNotSupportedError,
)


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
