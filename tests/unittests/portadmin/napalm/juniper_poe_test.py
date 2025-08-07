import pytest
from unittest.mock import Mock

from lxml import etree

from nav.portadmin.handlers import (
    POEStateNotSupportedError,
    POENotSupportedError,
    XMLParseError,
)
from nav.portadmin.napalm.juniper import Juniper


def test_returns_correct_state_options(handler_mock):
    state_options = handler_mock.get_poe_state_options()
    assert Juniper.POE_ENABLED in state_options
    assert Juniper.POE_DISABLED in state_options


def test_state_converter_returns_correct_states(handler_mock):
    assert handler_mock._poe_string_to_state("enabled") == Juniper.POE_ENABLED
    assert handler_mock._poe_string_to_state("disabled") == Juniper.POE_DISABLED


def test_state_converter_raises_error_for_invalid_states(handler_mock):
    with pytest.raises(POEStateNotSupportedError):
        handler_mock._poe_string_to_state("invalid_state")


class TestGetPoeStates:
    def test_interfaces_from_db_is_used_if_input_is_none(self, handler_mock, xml_bulk):
        expected_interfaces = handler_mock.netbox.interfaces
        handler_mock._get_all_poe_interface_information = Mock(return_value=xml_bulk)
        return_dict = handler_mock.get_poe_states()
        for interface in expected_interfaces:
            assert interface.ifname in return_dict

    def test_interfaces_from_db_is_used_if_input_is_empty(self, handler_mock, xml_bulk):
        expected_interfaces = handler_mock.netbox.interfaces
        handler_mock._get_all_poe_interface_information = Mock(return_value=xml_bulk)
        return_dict = handler_mock.get_poe_states([])
        for interface in expected_interfaces:
            assert interface.ifname in return_dict

    def test_returns_empty_dict_if_no_input_and_no_interfaces_in_db(
        self, handler_mock, xml_bulk
    ):
        handler_mock.netbox.interfaces = []
        return_dict = handler_mock.get_poe_states()
        assert return_dict == {}

    def test_returns_correct_state_if_input_has_one_interface(
        self, handler_mock, xml, interface1_mock
    ):
        handler_mock._get_poe_interface_information = Mock(return_value=xml)
        return_dict = handler_mock.get_poe_states([interface1_mock])
        assert return_dict[interface1_mock.ifname] == handler_mock.POE_ENABLED

    def test_returns_correct_states_if_input_has_multiple_interfaces(
        self, handler_mock, xml_bulk, interface1_mock, interface2_mock
    ):
        handler_mock._get_all_poe_interface_information = Mock(return_value=xml_bulk)
        return_dict = handler_mock.get_poe_states([interface1_mock, interface2_mock])
        assert return_dict[interface1_mock.ifname] == Juniper.POE_ENABLED
        assert return_dict[interface2_mock.ifname] == Juniper.POE_DISABLED

    def test_returns_none_for_single_interface_that_does_not_support_poe(
        self, handler_mock, interface1_mock
    ):
        handler_mock._get_single_poe_state = Mock(side_effect=POENotSupportedError)
        return_dict = handler_mock.get_poe_states([interface1_mock])
        assert return_dict[interface1_mock.ifname] is None

    def test_returns_none_for_multiple_interfaces_that_does_not_support_poe(
        self, handler_mock, interface1_mock, interface2_mock
    ):
        bulk_return_dict = {interface1_mock.ifname: None, interface2_mock.ifname: None}
        handler_mock._get_poe_states_bulk = Mock(return_value=bulk_return_dict)
        return_dict = handler_mock.get_poe_states([interface1_mock, interface2_mock])
        assert return_dict[interface1_mock.ifname] is None
        assert return_dict[interface2_mock.ifname] is None


class TestGetSinglePoeState:
    def test_returns_correct_state_for_interface_that_exists_in_xml_response(
        self, handler_mock, xml, interface1_mock
    ):
        handler_mock._get_poe_interface_information = Mock(return_value=xml)
        state = handler_mock._get_single_poe_state(interface1_mock)
        assert state == Juniper.POE_ENABLED

    def test_raises_exception_if_no_interfaces_in_xml(
        self, handler_mock, interface1_mock, xml_empty
    ):
        handler_mock._get_poe_interface_information = Mock(return_value=xml_empty)
        with pytest.raises(POENotSupportedError):
            handler_mock._get_single_poe_state(interface1_mock)

    def test_raises_exception_if_multiple_interfaces_in_xml(
        self, handler_mock, interface1_mock, xml_bulk_wrong_format
    ):
        handler_mock._get_poe_interface_information = Mock(
            return_value=xml_bulk_wrong_format
        )
        with pytest.raises(XMLParseError):
            handler_mock._get_single_poe_state(interface1_mock)


class TestGetPoeStatesBulk:
    def test_returns_correct_states(
        self, handler_mock, xml_bulk, interface1_mock, interface2_mock
    ):
        handler_mock._get_all_poe_interface_information = Mock(return_value=xml_bulk)
        states = handler_mock._get_poe_states_bulk([interface1_mock, interface2_mock])
        assert states[interface1_mock.ifname] == Juniper.POE_ENABLED
        assert states[interface2_mock.ifname] == Juniper.POE_DISABLED

    def test_maps_interface_to_none_if_poe_not_supported(self, handler_mock, xml_bulk):
        handler_mock._get_all_poe_interface_information = Mock(return_value=xml_bulk)
        if_mock = Mock()
        if_mock.ifname == "random_if"
        if_mock.ifindex = 0
        states = handler_mock._get_poe_states_bulk([if_mock])
        assert states[if_mock.ifname] is None

    def test_returns_none_values_if_no_interfaces_in_xml(
        self, handler_mock, interface1_mock, interface2_mock, xml_empty
    ):
        handler_mock._get_all_poe_interface_information = Mock(return_value=xml_empty)
        return_dict = handler_mock._get_poe_states_bulk(
            [interface1_mock, interface2_mock]
        )
        assert return_dict[interface1_mock.ifname] is None
        assert return_dict[interface2_mock.ifname] is None


@pytest.fixture()
def xml(interface1_mock):
    """Creates a ElementTree containing poe information for one interface"""
    tree_string = f"""
        <poe>
            <interface-information-detail>
                <interface-name-detail>{interface1_mock.ifname}</interface-name-detail>
                <interface-enabled-detail>Enabled</interface-enabled-detail>
            </interface-information-detail>
        </poe>"""
    tree = etree.fromstring(tree_string)
    yield tree


@pytest.fixture()
def xml_bulk_wrong_format(interface1_mock, interface2_mock):
    """
    Creates a ElementTree with the format meant for a single interface in the response,
    but it contains poe information for two interfaces
    """
    tree_string = f"""
        <poe>
            <interface-information-detail>
                <interface-name-detail>{interface1_mock.ifname}</interface-name-detail>
                <interface-enabled-detail>Enabled</interface-enabled-detail>
            </interface-information-detail>
            <interface-information-detail>
                <interface-name-detail>{interface2_mock.ifname}</interface-name-detail>
                <interface-enabled-detail>Enabled</interface-enabled-detail>
            </interface-information-detail>
        </poe>"""
    tree = etree.fromstring(tree_string)
    yield tree


@pytest.fixture()
def xml_bulk(interface1_mock, interface2_mock):
    """Creates a ElementTree containing poe information for two interfaces"""
    tree_string = f"""
        <poe>
            <interface-information>
                <interface-name>{interface1_mock.ifname}</interface-name>
                <interface-enabled>Enabled</interface-enabled>
            </interface-information>
            <interface-information>
                <interface-name>{interface2_mock.ifname}</interface-name>
                <interface-enabled>Disabled</interface-enabled>
            </interface-information>
        </poe>"""
    tree = etree.fromstring(tree_string)
    yield tree


@pytest.fixture()
def xml_empty():
    """Creates a ElementTree containing no poe state for any interface"""
    tree_string = """
        <poe>
        </poe>"""
    tree = etree.fromstring(tree_string)
    yield tree
