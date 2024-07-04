from collections import deque
from nav.dhcp.kea_metrics import *
import pytest
import requests
from IPy import IP
import json
import logging
import re
from requests.exceptions import JSONDecodeError, HTTPError, Timeout

class TestSendQuery:
    """Testing the list[KeaResponse] returned by send_query()"""
    def test_response_with_success_status_should_succeed_and_be_logged(self, success_response, enqueue_post_response, testlog):
        enqueue_post_response("command", success_response)
        testlog.clear()
        responses = send_dummy_query("command")
        assert len(responses) == 4
        for response in responses:
            assert response.success
            assert isinstance(response.text, str)
            assert isinstance(response.arguments, dict)
            assert isinstance(response.service, str)
        assert testlog.has_entries(logging.DEBUG, regexes=("query", "sen(d|t)", "192.0.2.2:80"))

    def test_response_with_error_status_should_succeed_and_be_logged(self, error_response, enqueue_post_response, testlog):
        enqueue_post_response("command", error_response)
        responses = send_dummy_query("command")
        assert len(responses) == 5
        for response in responses:
            assert not response.success
            assert isinstance(response.text, str)
            assert isinstance(response.arguments, dict)
            assert isinstance(response.service, str)
        assert testlog.has_entries(logging.DEBUG, regexes=("sen(d|t)[^:]", "[^_]query", "192.0.2.2:80"))
        assert testlog.has_entries(logging.DEBUG, n=1)

    def test_exceptions_should_be_logged_and_reraised_as_KeaError(self, enqueue_post_response, testlog):
        enqueue_post_response("httperror", raiser(HTTPError))
        enqueue_post_response("timeout", raiser(Timeout))
        query = KeaQuery("httperror", [], {})
        with pytest.raises(KeaError):
            responses = send_query(query, "192.0.2.2", 80)
        assert testlog.has_entries(logging.DEBUG, regexes=("sen(d|t)[^:]", "[^_]query", "192.0.2.2:80"))
        assert testlog.has_entries(logging.DEBUG, regexes=("query", "fail|error|exception", "192.0.2.2:80"))

        testlog.clear()

        query = KeaQuery("timeout", [], {})
        with pytest.raises(KeaError):
            responses = send_query(query, "192.0.2.2", 80)
        assert testlog.has_entries(logging.DEBUG, regexes=("sen(d|t)[^:]", "[^_]query", "192.0.2.2:80"))
        assert testlog.has_entries(logging.DEBUG, regexes=("[^_]query", "fail|error|exception", "192.0.2.2:80"))

    def test_response_with_invalid_json_should_raise_and_be_logged(self, invalid_json_response, enqueue_post_response, testlog):
        enqueue_post_response("command", invalid_json_response)
        testlog.clear()
        with pytest.raises(KeaError):
            responses = send_dummy_query("command")
        assert testlog.has_entries(logging.DEBUG, regexes=("sen(d|t)[^:]", "[^_]query", "192.0.2.2:80"))
        assert testlog.has_entries(logging.DEBUG, regexes=("invalid", "json", "192.0.2.2:80"))

class TestProcessingJsonIntoDataclass:
    """
    Testing that json formatted Kea DHCP configuration is correctly processed
    into python dataclasses
    """
    def test_dhcp4_config_json_should_be_correctly_processed_into_KeaDhcpConfig(
            self,
            dhcp4_config,
            dhcp4_config_with_shared_networks
    ):
        # Massaging and processing json with subnet4 list
        j = json.loads(dhcp4_config)
        config = KeaDhcpConfig.from_json(j)
        assert len(config.subnets) == 1
        subnet = config.subnets[0]
        assert subnet.id == 1
        assert subnet.prefix == IP("192.0.0.0/8")
        assert len(subnet.pools) == 2
        assert subnet.pools[0] == (IP("192.1.0.1"), IP("192.1.0.200"))
        assert subnet.pools[1] == (IP("192.3.0.1"), IP("192.3.0.200"))
        assert config.dhcp_version == 4
        assert config.config_hash is None

        # Massaging and processing json with shared_networks list AND subnet4 list
        j = json.loads(dhcp4_config_with_shared_networks)
        config = KeaDhcpConfig.from_json(j)
        assert len(config.subnets) == 4
        subnets = {subnet.id: subnet for subnet in config.subnets}

        subnet1 = subnets[1]
        assert subnet1.id == 1
        assert subnet1.prefix == IP("192.0.1.0/24")
        assert len(subnet1.pools) == 1
        assert subnet1.pools[0] == (IP("192.0.1.1"), IP("192.0.1.200"))
        assert config.dhcp_version == 4
        assert config.config_hash is None

        subnet2 = subnets[2]
        assert subnet2.id == 2
        assert subnet2.prefix == IP("192.0.2.0/24")
        assert len(subnet2.pools) == 1
        assert subnet2.pools[0] == (IP("192.0.2.100"), IP("192.0.2.199"))
        assert config.dhcp_version == 4
        assert config.config_hash is None

        subnet3 = subnets[3]
        assert subnet3.id == 3
        assert subnet3.prefix == IP("192.0.3.0/24")
        assert len(subnet3.pools) == 1
        assert subnet3.pools[0] == (IP("192.0.3.100"), IP("192.0.3.199"))
        assert config.dhcp_version == 4
        assert config.config_hash is None

        subnet4 = subnets[4]
        assert subnet4.id == 4
        assert subnet4.prefix == IP("10.0.0.0/8")
        assert len(subnet4.pools) == 1
        assert subnet4.pools[0] == (IP("10.0.0.1"), IP("10.0.0.99"))
        assert config.dhcp_version == 4
        assert config.config_hash is None

    def test_dhcp6_config_json_should_be_correctly_processed_into_KeaDhcpConfig(self, dhcp6_config):
        j = json.loads(dhcp6_config)
        config = KeaDhcpConfig.from_json(j)
        assert len(config.subnets) == 2
        subnet1 = config.subnets[0]
        assert subnet1.id == 1
        assert subnet1.prefix == IP("2001:db8:1:1::/64")
        assert len(subnet1.pools) == 1
        assert subnet1.pools[0] == (IP("2001:db8:1:1::1"), IP("2001:db8:1:1::ffff"))
        assert config.dhcp_version == 6
        assert config.config_hash is None

        subnet2 = config.subnets[1]
        assert subnet2.id == 2
        assert subnet2.prefix == IP("2001:db8:1:2::/64")
        assert len(subnet2.pools) == 2
        assert subnet2.pools[0] == (IP("2001:db8:1:2::1"), IP("2001:db8:1:2::ffff"))
        assert subnet2.pools[1] == (IP("2001:db8:1:2::1:0"), IP("2001:db8:1:2::1:ffff"))
        assert config.dhcp_version == 6
        assert config.config_hash is None

"""
def test_invalid_json_response(testlog, invalid_json_response, enqueue_post_response):
    enqueue_post_response("config-get", lambda **_: invalid_json_response)
    enqueue_post_response("statistic-get", lambda **_: invalid_json_response)
    testlog.clear()
    source = KeaDhcpMetricSource(address="192.0.2.1", port=80)
    with pytest.raises(KeaError):
        source.fetch_and_set_dhcp_config()
    assert testlog.has_entries(logging.DEBUG, regex=".*invalid.*json.*")

    # fetch_dhcp_config_hash should not raise when the server does not support
    # config-hash-get command
    testlog.clear()
    h = source.fetch_dhcp_config_hash()
    assert h == None
    assert testlog.has_entries(
        logging.DEBUG, regex=".*no.*support.*hash.*|.*hash.*no.*support.*"
    )

    # fetch_dhcp_config_hash should raise when the server returns invalid
    # json
    enqueue_post_response("config-hash-get", lambda **_: invalid_json_response)
    testlog.clear()
    with pytest.raises(KeaError):
        source.fetch_and_set_dhcp_config()
    assert testlog.has_entries(logging.DEBUG, regex=".*invalid.*json.*")

    # FUNCTIONS USED EXTERNALLY SHOULD CATCH EXCEPTIONS AND LOG WARNINGS
    # fetch_metrics is a method also used external to the module, and thus
    # instead of raising it should log when the server returns invalid json
    testlog.clear()
    source.fetch_metrics()
    assert testlog.has_entries(logging.WARNING, JSONDecodeError, n=1)
"""

class TestKeaDhcpMetricSource:
    def test_when_no_cached_KeaDhcpConfig_exist_should_fetch_and_set_correct_KeaDhcpConfig(
            self,
            dhcp4_config,
            dhcp4_config_with_shared_networks,
            dhcp6_config,
            enqueue_post_response,
            testlog,
    ):
        for config_string in dhcp4_config, dhcp6_config, dhcp4_config_with_shared_networks:
            testlog.clear()
            enqueue_post_response("config-get", response_json(config_string))
            source = KeaDhcpMetricSource("192.0.2.1", 80, https=False)
            assert source.kea_dhcp_config is None
            config = source.fetch_and_set_dhcp_config()
            actual_config = KeaDhcpConfig.from_json(
                json.loads(config_string)
            )
            assert config == actual_config
            assert source.kea_dhcp_config == actual_config
            assert testlog.has_entries(logging.DEBUG, regexes=("sen(d|t)[^:]", "[^_]query", "192.0.2.1"))

    def test_when_cached_KeaDhcpConfig_exist_and_local_hash_match_with_server_hash_should_not_fetch_new_KeaDhcpConfig(
            self,
            dhcp4_config,
            dhcp4_config_with_shared_networks,
            enqueue_post_response,
    ):
        enqueue_post_response("config-get", response_json(dhcp4_config))
        source = KeaDhcpMetricSource("192.0.2.1", 80, https=False)
        source.fetch_and_set_dhcp_config()
        enqueue_post_response("config-hash-get", response_json(f'{{hash: "{source.kea_dhcp_config.config_hash}"}}'))
        # The command 'config-hash-get' is set to return the same hash as is already cached. Thus, the test should fail if 'config-get' is queried.
        enqueue_post_response("config-get", lambda **_: pytest.fail())
        source.fetch_and_set_dhcp_config()

    def test_when_cached_KeaDhcpConfig_exist_and_local_hash_doesnt_match_with_server_hash_should_fetch_new_KeaDhcpConfig(
            self,
            dhcp4_config,
            dhcp4_config_with_shared_networks,
            enqueue_post_response,
    ):
        enqueue_post_response("config-get", response_json(dhcp4_config))
        source = KeaDhcpMetricSource("192.0.2.1", 80, https=False)
        source.fetch_and_set_dhcp_config()
        assert source.kea_dhcp_config == KeaDhcpConfig.from_json(dhcp4_config)

        old_hash = source.kea_dhcp_config.config_hash
        new_hash = "0" + old_hash[1:] if old_hash[0] != "0" else "1" + old_hash[1:]

        enqueue_post_response("config-hash-get", response_json(f'{{hash: "{new_hash}"}}'))
        enqueue_post_response("config-get", response_json(dhcp4_config_with_shared_networks))
        source.fetch_and_set_dhcp_config()
        assert source.kea_dhcp_config == KeaDhcpConfig.from_json(dhcp4_config_with_shared_networks)
    
        
# @pytest.fixture
# @enqueue_post_response
# def dhcp4_config_response_result_is_1():
#     return f'''
#     {{
#         "result": 1,
#         "arguments": {{
#             {DHCP4_CONFIG}
#         }}
#     }}
#     '''

# def test_get_dhcp_config_result_is_1(dhcp4_config_result_is_1):
#     with pytest.raises(Exception): # TODO: Change
#         get_dhcp_server("example-org", dhcp_version=4)


@pytest.fixture
def testlog(caplog):
    caplog.clear()
    caplog.set_level(logging.DEBUG)
    return LogChecker(caplog)


class LogChecker:
    def __init__(self, caplog):
        self.caplog = caplog

    def clear(self):
        self.caplog.clear()

    def has_entries(self, level, exception=None, regexes=None, n=None):
        """
        Check if there is any log entries of logging level `level`, optionally
        made for an exception `exception`, optionally with all regexes in
        `regexes` fully matching some substring of the log message, and
        optionally requiring that there is exactly `n` such records logged.
        """

        def causes(e: BaseException):
            while e:
                yield type(e)
                e = e.__cause__

        entries = [
            entry
            for entry in self.caplog.records
            if entry.levelno >= level
            and (
                exception is None
                or entry.exc_info is not None
                and exception in causes(entry.exc_info[1])
            )
            and (regexes is None or all(re.search(regex, entry.message.lower(), re.DOTALL) for regex in regexes))
        ]
        return n is None and len(entries) > 0 or len(entries) == n


def response_json(string):
    return f'''
    [
    {{
        "result": 0,
        "arguments": {string}
    }}
    ]
    '''




@pytest.fixture
def dhcp6_config():
    return '''{
"Dhcp6": {
    "valid-lifetime": 4000,
    "renew-timer": 1000,
    "rebind-timer": 2000,
    "preferred-lifetime": 3000,

    "interfaces-config": {
        "interfaces": [ "eth0" ]
    },

    "lease-database": {
        "type": "memfile",
        "persist": true,
        "name": "/var/lib/kea/dhcp6.leases"
    },

    "subnet6": [
        {
            "id": 1,
            "subnet": "2001:db8:1:1::/64",
            "pools": [
                {
                    "pool": "2001:db8:1:1::1-2001:db8:1:1::ffff"
                }
             ]
        },
        {
            "id": 2,
            "subnet": "2001:db8:1:2::/64",
            "pools": [
                {
                    "pool": "2001:db8:1:2::1-2001:db8:1:2::ffff"
                },
                {
                    "pool": "2001:db8:1:2::1:0/112"
                }
             ]
        }
    ]
}
}'''

@pytest.fixture
def dhcp4_config():
    return '''
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


@pytest.fixture
def dhcp4_config_with_shared_networks():
    return '''{
            "Dhcp4": {
                "shared-networks": [
                     {
                         "name": "shared-network-1",
                         "subnet4": [
                             {
                                 "id": 4,
                                 "subnet": "10.0.0.0/8",
                                 "pools": [ { "pool":  "10.0.0.1 - 10.0.0.99" } ]
                             },
                             {
                                 "id": 3,
                                 "subnet": "192.0.3.0/24",
                                 "pools": [ { "pool":  "192.0.3.100 - 192.0.3.199" } ]
                             }
                         ]
                     },
                     {
                         "name": "shared-network-2",
                         "subnet4": [
                             {
                                 "id": 2,
                                 "subnet": "192.0.2.0/24",
                                 "pools": [ { "pool":  "192.0.2.100 - 192.0.2.199" } ]
                             }
                         ]
                     }
                 ],
                "subnet4": [{
                "id": 1,
                "subnet": "192.0.1.0/24",
                "pools": [
                    {
                        "pool": "192.0.1.1 - 192.0.1.200"
                    }
                ]
                }]
            }
        }'''


@pytest.fixture(autouse=True)
def enqueue_post_response(monkeypatch):
    """
    Any test that include this fixture, gets access to a function that
    can be used to append text strings to a fifo queue of post
    responses that in fifo order will be returned as proper Response
    objects by calls to requests.post and requests.Session().post.

    This is how we mock what would otherwise be post requests to a
    server.
    """
    # Dictonary of fifo queues, keyed by command name. A queue stored with key K has the textual content of the responses we want to return (in fifo order, one per call) on a call to requests.post with data that represents a Kea Control Agent command K
    command_responses = {}
    unknown_command_response = """[
  {{
    "result": 2,
    "text": "'{0}' command not supported."
  }}
]"""

    def new_post_function(url, *args, data="{}", **kwargs):
        if isinstance(data, dict):
            data = json.dumps(data)
        elif isinstance(data, bytes):
            data = data.decode("utf8")
        if not isinstance(data, str):
            pytest.fail(
                f"data argument to the mocked requests.post() is of unknown type {type(data)}"
            )

        try:
            data = json.loads(data)
            command = data["command"]
        except (JSONDecodeError, KeyError):
            pytest.fail(
                "All post requests that the Kea Control Agent receives from NAV"
                "should be a JSON with a 'command' key. Instead, the mocked Kea "
                f"Control Agent received {data!r}"
            )

        fifo = command_responses.get(command, deque())
        if fifo:
            first = fifo[0]
            if callable(first):
                text = first(arguments=data.get("arguments", {}), service=data.get("service", []))
            else:
                text = str(first)
                fifo.popleft()
        else:
            text = unknown_command_response.format(command)

        response = requests.Response()
        response._content = text.encode("utf8")
        response.encoding = "utf8"
        response.status_code = 400
        response.reason = "OK"
        response.headers = kwargs.get("headers", {})
        response.cookies = kwargs.get("cookies", {})
        response.url = url
        response.close = lambda: True
        return response

    def new_post_method(self, url, *args, **kwargs):
        return new_post_function(url, *args, **kwargs)

    def add_command_response(command_name, text):
        command_responses.setdefault(command_name, deque())
        command_responses[command_name].append(text)

    monkeypatch.setattr(requests, 'post', new_post_function)
    monkeypatch.setattr(requests.Session, 'post', new_post_method)

    return add_command_response


@pytest.fixture
def success_response():
    return '''[
    {"result": 0, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 0, "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 0, "service": "d"},
    {"result": 0}
    ]'''


@pytest.fixture
def error_response():
    return '''[
    {"result": 1, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 2, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 3, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 4, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"text": "b", "arguments": {"arg1": "val1"}, "service": "d"}
    ]'''


@pytest.fixture
def invalid_json_response():
    return '''[
    {"result": 1, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 2, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 3, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"result": 4, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"},
    {"text": "b", "arguments": {"arg1": "val1"}, "service": "d"
    ]'''

def send_dummy_query(command="command"):
    return send_query(
        query=KeaQuery(command, [], {}),
        address="192.0.2.2",
        port=80,
    )

def raiser(exception: type[Exception]):
    def do_raise(*args, **kwargs):
        raise exception
    return do_raise
