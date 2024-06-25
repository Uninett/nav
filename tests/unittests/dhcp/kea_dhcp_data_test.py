from nav.dhcp.kea_dhcp_data import *
import pytest
import requests
from IPy import IP
import json
from requests.exceptions import JSONDecodeError

DHCP4_CONFIG = '''
    {
        "Dhcp4": {
            "subnet4": [{
            "4o6-interface": "eth1",
            "4o6-interface-id": "ethx",
            "4o6-subnet": "2001:db8:1:1::/64",
            "allocator": "iterative",
            "authoritative": false,
            "boot-file-name": "/tmp/boot",
            "client-class": "foobar",
            "ddns-generated-prefix": "myhost",
            "ddns-override-client-update": true,
            "ddns-override-no-update": true,
            "ddns-qualifying-suffix": "example.org",
            "ddns-replace-client-name": "never",
            "ddns-send-updates": true,
            "ddns-update-on-renew": true,
            "ddns-use-conflict-resolution": true,
            "hostname-char-replacement": "x",
            "hostname-char-set": "[^A-Za-z0-9.-]",
            "id": 1,
            "interface": "eth0",
            "match-client-id": true,
            "next-server": "0.0.0.0",
            "store-extended-info": true,
            "option-data": [
                {
                    "always-send": true,
                    "code": 3,
                    "csv-format": true,
                    "data": "192.0.3.1",
                    "name": "routers",
                    "space": "dhcp4"
                }
            ],
            "pools": [
                {
                    "client-class": "phones_server1",
                    "option-data": [],
                    "pool": "192.1.0.1 - 192.1.0.200",
                    "pool-id": 7,
                    "require-client-classes": [ "late" ]
                },
                {
                    "client-class": "phones_server2",
                    "option-data": [],
                    "pool": "192.3.0.1 - 192.3.0.200",
                    "require-client-classes": []
                }
            ],
            "rebind-timer": 40,
            "relay": {
                "ip-addresses": [
                    "192.168.56.1"
                ]
            },
            "renew-timer": 30,
            "reservations-global": true,
            "reservations-in-subnet": true,
            "reservations-out-of-pool": true,
            "calculate-tee-times": true,
            "t1-percent": 0.5,
            "t2-percent": 0.75,
            "cache-threshold": 0.25,
            "cache-max-age": 1000,
            "reservations": [
                {
                    "circuit-id": "01:11:22:33:44:55:66",
                    "ip-address": "192.0.2.204",
                    "hostname": "foo.example.org",
                    "option-data": [
                        {
                            "name": "vivso-suboptions",
                            "data": "4491"
                        }
                    ]
                }
            ],
            "require-client-classes": [ "late" ],
            "server-hostname": "myhost.example.org",
            "subnet": "192.0.0.0/8",
            "valid-lifetime": 6000,
            "min-valid-lifetime": 4000,
            "max-valid-lifetime": 8000
            }]
        }
    }
    '''

def custom_post_response(func):
    """
    Replace the content of the response from any call to requests.post()
    with the content of func().encode("utf8")
    """
    def new_post(url, *args, **kwargs):
        response = requests.Response()
        response._content = func().encode("utf8")
        response.encoding = "utf8"
        response.status_code = 400
        response.reason = "OK"
        response.headers = kwargs.get("headers", {})
        response.cookies = kwargs.get("cookies", {})
        response.url = url
        response.close = lambda: True
        return response

    def new_post_method(self, url, *args, **kwargs):
        return new_post(url, *args, **kwargs)

    def replace_post(monkeypatch):
        monkeypatch.setattr(requests, 'post', new_post)
        monkeypatch.setattr(requests.Session, 'post', new_post_method) # Not sure this works?

    return replace_post

@pytest.fixture
@custom_post_response
def success_responses():
    return '''[
    {"result": 0, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 0, "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 0, "service": "d"},
    {"result": 0}
    ]'''

@pytest.fixture
@custom_post_response
def error_responses():
    return '''[
    {"result": 1, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 2, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 3, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 4, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"text": "b", "arguments": {"arg1": "val1"}, "service": "d"}
    ]'''

@pytest.fixture
@custom_post_response
def invalid_json_responses():
    return '''[
    {"result": 1, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 2, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 3, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 4, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"text": "b", "arguments": {"arg1": "val1"}, "service": "d"
    ]'''

@pytest.fixture
@custom_post_response
def large_responses():
    return '''

    '''

def test_success_responses_does_succeed(success_responses):
    query = KeaQuery("command", {}, [])
    responses = send_query(query, "example.org")
    assert len(responses) == 4
    for response in responses:
        assert response.success

def test_error_responses_does_not_succeed(error_responses):
    query = KeaQuery("command", {}, [])
    responses = send_query(query, "example.org")
    assert len(responses) == 5
    for response in responses:
        assert not response.success

def test_invalid_json_responses_raises_jsonerror(invalid_json_responses):
    query = KeaQuery("command", {}, [])
    with pytest.raises(JSONDecodeError):
        responses = send_query(query, "example.org")

def test_correct_subnet_from_json(dhcp4_config):
    j = json.loads(dhcp4_config)
    subnet = Subnet.from_json(j["Dhcp4"]["subnet4"][0])
    assert subnet.id == 1
    assert subnet.prefix == IP("192.0.0.0/8")
    assert len(subnet.pools) == 2
    assert subnet.pools[0] == (IP("192.1.0.1"), IP("192.1.0.200"))
    assert subnet.pools[1] == (IP("192.3.0.1"), IP("192.3.0.200"))

def test_correct_config_from_json(dhcp4_config):
    j = json.loads(dhcp4_config)
    config = KeaDhcpConfig.from_json(j)
    assert len(config.subnets) == 1
    subnet = config.subnets[0]
    assert subnet.id == 1
    assert subnet.prefix == IP("192.0.0.0/8")
    assert len(subnet.pools) == 2
    assert subnet.pools[0] == (IP("192.1.0.1"), IP("192.1.0.200"))
    assert subnet.pools[1] == (IP("192.3.0.1"), IP("192.3.0.200"))
    assert config.ip_version == 4

@pytest.fixture
@custom_post_response
def dhcp4_config_response():
    return f'''
    {{
        "result": 0,
        "arguments": {{
            {DHCP4_CONFIG}
        }}
    }}
    '''

def test_get_dhcp_config(dhcp4_config_response):
    config = get_dhcp_server("example.org", ip_version=4)
    assert len(config.subnets) == 1
    subnet = config.subnets[0]
    assert subnet.id == 1
    assert subnet.prefix == IP("192.0.0.0/8")
    assert len(subnet.pools) == 2
    assert subnet.pools[0] == (IP("192.1.0.1"), IP("192.1.0.200"))
    assert subnet.pools[1] == (IP("192.3.0.1"), IP("192.3.0.200"))
    assert config.ip_version == 4

@pytest.fixture
@custom_post_response
def dhcp4_config_response_result_is_1():
    return f'''
    {{
        "result": 1,
        "arguments": {{
            {DHCP4_CONFIG}
        }}
    }}
    '''

def test_get_dhcp_config_result_is_1(dhcp4_config_result_is_1):
    with pytest.raises(Exception): # TODO: Change
        get_dhcp_server("example-org", ip_version=4)
