from collections import deque
from nav.dhcp.kea_metrics import *
import pytest
import requests
from IPy import IP
import json
import logging
import re
from requests.exceptions import JSONDecodeError, HTTPError, Timeout


def test_should_return_all_metrics_from_normal_responses():



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


def raiser(exception: type[Exception]):
    def do_raise(*args, **kwargs):
        raise exception
    return do_raise

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
def DHCP6_CONFIG():
    config = {
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
    }
    statistics = {
                "subnet[1].assigned-addresses": [
                  [
                    1,
                    "2024-07-22 09:06:58.140438"
                  ],
                  [
                    0,
                    "2024-07-05 20:44:54.230608"
                  ],
                  [
                    1,
                    "2024-07-05 09:15:05.626594"
                  ],
                ],
                "subnet[1].cumulative-assigned-addresses": [
                  [
                    6,
                    "2024-07-22 09:06:58.140441"
                  ],
                  [
                    5,
                    "2024-07-05 09:15:05.626595"
                  ],
                  [
                    4,
                    "2024-07-04 09:18:47.679802"
                  ]
                ],
                "subnet[1].declined-addresses": [
                  [
                    0,
                    "2024-07-03 16:13:59.401071"
                  ]
                ],
                "subnet[1].reclaimed-declined-addresses": [
                  [
                    0,
                    "2024-07-03 16:13:59.401073"
                  ]
                ],
                "subnet[1].reclaimed-leases": [
                  [
                    5,
                    "2024-07-05 20:44:54.230614"
                  ],
                  [
                    4,
                    "2024-07-04 16:29:36.612043"
                  ],
                  [
                    3,
                    "2024-07-04 14:22:18.181720"
                  ]
                ],
                "subnet[1].total-addresses": [
                  [
                    239,
                    "2024-07-03 16:13:59.401058"
                  ]
                ],
                "subnet[1].v4-reservation-conflicts": [
                  [
                    0,
                    "2024-07-03 16:13:59.401062"
                  ]
                ],
    }

    metrics = [
        DhcpMetric("1970-01-01 01:00:01.000000000", 
    ]


DHCP6_CONFIG_STATISTICS =

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

DHCP4_CONFIG_WITH_SHARED_NETWORKS = '''{
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
