from collections import defaultdict

from mock import Mock
from twisted.names import dns
from twisted.names.error import DNSNameError

from nav.asyncdns import ForwardResolver, Resolver

BUICK_NAME = "buick.lab.uninett.no"


def test_forward_lookup_should_work_with_ipv4_results():
    record = Mock()
    record.name = BUICK_NAME
    record.type = dns.A
    record.payload.address = b"\xac\x00\x00\x01"
    result = [[record]]
    result_name, address_list = ForwardResolver._extract_records(result, BUICK_NAME)

    assert result_name == BUICK_NAME
    assert address_list == ["172.0.0.1"]


def test_forward_lookup_should_work_with_ipv6_results():
    record = Mock()
    record.name = BUICK_NAME
    record.type = dns.AAAA
    record.payload.address = b" \x01\r\xb833DDUUffww\x88\x88"
    result = [[record]]
    result_name, address_list = ForwardResolver._extract_records(result, BUICK_NAME)

    assert result_name == BUICK_NAME
    assert address_list == ["2001:db8:3333:4444:5555:6666:7777:8888"]


def test_forward_lookup_should_work_with_different_case_name_results():
    record = Mock()
    record.name = "bUiCk.LaB.uNiNeTt.No"
    record.type = dns.A
    record.payload.address = b"\x9e&\x98\xa2"
    result = [[record]]
    result_name, address_list = ForwardResolver._extract_records(result, BUICK_NAME)

    assert result_name == BUICK_NAME
    assert address_list == ["158.38.152.162"]


class TestSaveResult:
    """Tests for Resolver._save_result"""

    def _make_resolver(self):
        """Returns a Resolver instance without triggering __init__'s side effects"""
        resolver = object.__new__(Resolver)
        resolver.results = defaultdict(list)
        return resolver

    def test_when_error_arrives_after_success_it_should_keep_addresses(self):
        resolver = self._make_resolver()
        resolver._save_result(("host", ["10.0.0.1"]))
        resolver._save_result(("host", DNSNameError()))
        assert resolver.results["host"] == ["10.0.0.1"]

    def test_when_success_arrives_after_error_it_should_not_raise(self):
        resolver = self._make_resolver()
        resolver._save_result(("host", DNSNameError()))
        resolver._save_result(("host", []))
        assert isinstance(resolver.results["host"], DNSNameError)

    def test_when_both_succeed_it_should_combine_results(self):
        resolver = self._make_resolver()
        resolver._save_result(("host", ["10.0.0.1"]))
        resolver._save_result(("host", ["::1"]))
        assert resolver.results["host"] == ["10.0.0.1", "::1"]

    def test_when_both_fail_it_should_store_first_error(self):
        resolver = self._make_resolver()
        first_error = DNSNameError()
        resolver._save_result(("host", first_error))
        resolver._save_result(("host", DNSNameError()))
        assert resolver.results["host"] is first_error
