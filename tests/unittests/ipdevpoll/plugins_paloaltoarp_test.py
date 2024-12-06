from unittest.mock import patch, Mock

import pytest_twisted
import pytest

from IPy import IP
from nav.ipdevpoll.plugins.paloaltoarp import PaloaltoArp, _parse_arp
from twisted.internet import defer
from twisted.web.client import Agent, Response

valid_http_response_body = b'''
    <response status="success">
    <result>
            <max>132000</max>
            <total>3</total>
            <timeout>1800</timeout>
            <dp>s3dp1</dp>
            <entries>
                <entry>
                    <status>  s  </status>
                    <ip>192.168.0.1</ip>
                    <mac>00:00:00:00:00:01</mac>
                    <ttl>100</ttl>
                    <interface>ae2</interface>
                    <port>ae2</port>
                </entry>
                <entry>
                    <status>  e  </status>
                    <ip>192.168.0.2</ip>
                    <mac>00:00:00:00:00:02</mac>
                    <ttl>200</ttl>
                    <interface>ae2</interface>
                    <port>ae2</port>
                </entry>
                <entry>
                    <status>  c  </status>
                    <ip>192.168.0.3</ip>
                    <mac>00:00:00:00:00:03</mac>
                    <ttl>300</ttl>
                    <interface>ae3.61</interface>
                    <port>ae3</port>
                </entry>
                <entry>
                    <status>  i  </status>
                    <ip>192.168.0.4</ip>
                    <mac>00:00:00:00:00:04</mac>
                    <ttl>400</ttl>
                    <interface>ae3.61</interface>
                    <port>ae3</port>
                </entry>
            </entries>
        </result>
    </response>
    '''


def test_parse_arp_should_correctly_parse_valid_http_response_body():
    assert _parse_arp(valid_http_response_body) == [
        ('ifindex', IP('192.168.0.1'), '00:00:00:00:00:01'),
        ('ifindex', IP('192.168.0.2'), '00:00:00:00:00:02'),
        ('ifindex', IP('192.168.0.3'), '00:00:00:00:00:03'),
    ]


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_get_paloalto_arp_mappings_should_return_arp_mappings_on_valid_http_response(
    paloaltoarp,
):
    with patch.object(
        PaloaltoArp, "_do_request", return_value=defer.succeed(valid_http_response_body)
    ):
        assert paloaltoarp._do_request.call_count == 0
        mappings = yield paloaltoarp._get_paloalto_arp_mappings(
            IP("0.0.0.0"), "abcdefghijklmnop"
        )
        assert sorted(mappings) == [
            ('ifindex', IP('192.168.0.1'), '00:00:00:00:00:01'),
            ('ifindex', IP('192.168.0.2'), '00:00:00:00:00:02'),
            ('ifindex', IP('192.168.0.3'), '00:00:00:00:00:03'),
        ]
        assert paloaltoarp._do_request.call_count == 1


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_get_paloalto_arp_mappings_should_return_empty_list_on_request_error(
    paloaltoarp,
):
    with patch.object(PaloaltoArp, "_do_request", return_value=defer.succeed(None)):
        mappings = yield paloaltoarp._get_paloalto_arp_mappings(
            IP("10.0.0.0"), "incorrect_key"
        )
        assert mappings == []


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_do_request_should_form_correct_api_query_url(paloaltoarp):
    mock_response = Mock(spec=Response)
    mock_agent = Mock(spec=Agent)
    mock_agent.request.return_value = defer.succeed(mock_response)

    sentinel = object()

    with (
        patch('nav.ipdevpoll.plugins.paloaltoarp.Agent', return_value=mock_agent),
        patch('twisted.web.client.readBody', return_value=sentinel),
    ):
        address = IP("127.0.0.1")
        key = "secret"

        result = yield paloaltoarp._do_request(address, key)

        expected_url = f"https://{address}/api/?type=op&cmd=<show><arp><entry+name+=+'all'/></arp></show>&key={key}".encode(
            "utf-8"
        )

        mock_agent.request.assert_called()
        args, kwargs = mock_agent.request.call_args
        assert expected_url in args

        assert result == sentinel


@pytest.fixture
def paloaltoarp():
    """
    No method in PaloaltoArp except PaloaltoArp.handle() utilize the state of an
    instance, so as long as we defer testing PaloaltoArp.handle() to integration
    tests, we can make do with a fully mocked internal state for the unit
    tests. (The reason we do not declare the methods as static, so that we can
    skip this mocking step when testing, is to not mess with logging
    granularity.)
    """
    return PaloaltoArp(Mock(), Mock(), Mock())
