from unittest.mock import patch, Mock

from IPy import IP
from nav.ipdevpoll.plugins.paloaltoarp import PaloaltoArp, parse_arp
from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks, succeed
from twisted.web.client import Agent, Response

mock_data = b'''
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


def test_parse_mappings():
    assert parse_arp(mock_data) == [
        ('ifindex', IP('192.168.0.1'), '00:00:00:00:00:01'),
        ('ifindex', IP('192.168.0.2'), '00:00:00:00:00:02'),
        ('ifindex', IP('192.168.0.3'), '00:00:00:00:00:03'),
    ]


@inlineCallbacks
def test_get_mappings():
    # Mocking the __init__ method
    with patch.object(PaloaltoArp, "__init__", lambda x: None):
        instance = PaloaltoArp()
        instance.config = {'paloaltoarp': {'abcdefghijklmnop': '0.0.0.0'}}

        # Mocking _do_request to return the mock_data when called
        with patch.object(
            PaloaltoArp, "_do_request", return_value=defer.succeed(mock_data)
        ):
            mappings = yield instance._get_paloalto_arp_mappings(
                "0.0.0.0", "abcdefghijklmnop"
            )

            assert mappings == [
                ('ifindex', IP('192.168.0.1'), '00:00:00:00:00:01'),
                ('ifindex', IP('192.168.0.2'), '00:00:00:00:00:02'),
                ('ifindex', IP('192.168.0.3'), '00:00:00:00:00:03'),
            ]


@inlineCallbacks
def test_do_request():
    mock_response = Mock(spec=Response)
    mock_agent = Mock(spec=Agent)
    mock_agent.request.return_value = succeed(mock_response)

    with patch(
        'nav.ipdevpoll.plugins.paloaltoarp.Agent', return_value=mock_agent
    ), patch('twisted.web.client.readBody', return_value="test content"):
        mock_address = "paloalto.example.org"
        mock_key = "secret"

        mock_netbox = Mock(sysname=mock_address, ip="127.0.0.1")

        plugin = PaloaltoArp(netbox=mock_netbox, agent=Mock(), containers=Mock())
        result = yield plugin._do_request(mock_address, mock_key)

        expected_url = f"https://{mock_address}/api/?type=op&cmd=<show><arp><entry+name+=+'all'/></arp></show>&key={mock_key}".encode(
            "utf-8"
        )
        mock_agent.request.assert_called()
        args, kwargs = mock_agent.request.call_args
        assert expected_url in args

        assert result == "test content"
