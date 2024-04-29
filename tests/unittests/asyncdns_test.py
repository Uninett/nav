from mock import Mock
from twisted.names import dns

from nav.asyncdns import ForwardResolver

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
