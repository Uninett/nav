from collections import deque
from nav.dhcp.kea_metrics import *
from nav.dhcp.generic_metrics import DhcpMetric
import pytest
import requests
from IPy import IP
import json
import logging
import re
from requests.exceptions import JSONDecodeError, HTTPError, Timeout
from datetime import timezone


def test_dhcp6_config_and_statistic_response_that_is_valid_should_return_every_metric(
    valid_dhcp6, responsequeue
):
    config, statistics, expected_metrics = valid_dhcp6
    responsequeue.prefill("dhcp6", config, statistics)
    source = KeaDhcpMetricSource("192.0.1.2", 80, dhcp_version=6, tzinfo=timezone.utc)
    assert set(source.fetch_metrics()) == set(expected_metrics)


def test_dhcp4_config_and_statistic_response_that_is_valid_should_return_every_metric(
    valid_dhcp4, responsequeue
):
    config, statistics, expected_metrics = valid_dhcp4
    responsequeue.prefill("dhcp4", config, statistics)
    source = KeaDhcpMetricSource("192.0.1.2", 80, dhcp_version=4, tzinfo=timezone.utc)
    assert set(source.fetch_metrics()) == set(expected_metrics)


@pytest.mark.parametrize(
    "status", [status for status in KeaStatus if status != KeaStatus.SUCCESS]
)
def test_config_response_with_error_status_should_raise_KeaError(
    valid_dhcp4, responsequeue, status
):
    """
    If Kea responds with an error while fetching the Kea DHCP's config during
    fetch_metrics(), we cannot continue further, so we fail.
    """
    config, statistics, _ = valid_dhcp4
    responsequeue.prefill("dhcp4", None, statistics)
    responsequeue.add("config-get", kearesponse(config, status=status))
    source = KeaDhcpMetricSource("192.0.1.2", 80, dhcp_version=4)
    with pytest.raises(KeaException):
        source.fetch_metrics()


def test_any_response_with_invalid_format_should_raise_KeaError(
    valid_dhcp4, responsequeue
):
    """
    If Kea responds with an invalid format (i.e. in an unrecognizable way), we
    should fail loudly, because chances are either the host we're sending
    requests to is not a Kea Control Agent, or there's a part of the API that
    we've not covered.
    """
    config, statistics, _ = valid_dhcp4
    source = KeaDhcpMetricSource("192.0.1.2", 80, dhcp_version=4)

    responsequeue.add("config-get", "{}")
    with pytest.raises(KeaException):
        source.fetch_metrics()

    responsequeue.clear()

    responsequeue.prefill("dhcp4", config, None)
    responsequeue.add("statistic-get", "{}")
    with pytest.raises(KeaException):
        source.fetch_metrics()

    responsequeue.clear()

    responsequeue.prefill("dhcp4", None, statistics)
    responsequeue.add("config-get", "{}")
    with pytest.raises(KeaException):
        source.fetch_metrics()

    responsequeue.clear()

    # config-hash-get is only called if some config-get includes a hash we can compare
    # with the next time we're attempting to fetch a config:
    config["Dhcp4"]["hash"] = "foo"
    responsequeue.prefill("dhcp4", config, statistics)
    responsequeue.add("config-hash-get", "{}")
    with pytest.raises(KeaException):
        source.fetch_metrics()


def test_all_responses_is_empty_but_valid_should_yield_no_metrics(
    valid_dhcp4, responsequeue
):
    """
    If the Kea DHCP server we query does not have any subnets configured, the
    correct thing to do is to return an empty iterable, (as opposed to failing).

    Likewise, if it returns no statistics for its configured subnets, the
    correct thing to do is to return an empty iterable.
    """
    config, statistics, _ = valid_dhcp4
    responsequeue.prefill("dhcp4", None, statistics)
    responsequeue.add("config-get", lambda **_: kearesponse({"Dhcp4": {}}))
    source = KeaDhcpMetricSource("192.0.1.2", 80, dhcp_version=4, tzinfo=timezone.utc)
    assert list(source.fetch_metrics()) == []

    responsequeue.clear()

    responsequeue.prefill("dhcp4", config, None)
    responsequeue.add(
        "statistic-get", lambda arguments, **_: kearesponse({arguments["name"]: []})
    )
    assert list(source.fetch_metrics()) == []

    responsequeue.clear()

    responsequeue.prefill("dhcp4", config, None)
    responsequeue.add("statistic-get", lambda **_: kearesponse({}))
    assert list(source.fetch_metrics()) == []


@pytest.fixture
def valid_dhcp6():
    config = {
        "Dhcp6": {
            "valid-lifetime": 4000,
            "renew-timer": 1000,
            "rebind-timer": 2000,
            "preferred-lifetime": 3000,
            "interfaces-config": {"interfaces": ["eth0"]},
            "lease-database": {
                "type": "memfile",
                "persist": True,
                "name": "/var/lib/kea/dhcp6.leases",
            },
            "subnet6": [
                {
                    "id": 1,
                    "subnet": "2001:db8:1:1::/64",
                    "pools": [{"pool": "2001:db8:1:1::1-2001:db8:1:1::ffff"}],
                },
                {
                    "id": 2,
                    "subnet": "2001:db8:1:2::/64",
                    "pools": [
                        {"pool": "2001:db8:1:2::1-2001:db8:1:2::ffff"},
                        {"pool": "2001:db8:1:2::1:0/112"},
                    ],
                },
            ],
            "shared-networks": [
                {
                    "name": "shared-network-1",
                    "subnet6": [
                        {
                            "id": 3,
                            "subnet": "2001:db8:1:3::/64",
                        },
                        {
                            "id": 4,
                            "subnet": "2001:db8:1:4::/64",
                        },
                    ],
                },
                {
                    "name": "shared-network-2",
                    "subnet6": [
                        {
                            "id": 5,
                            "subnet": "2001:db8:1:5::/64",
                        }
                    ],
                },
            ],
        }
    }
    statistics = {
        "subnet[1].assigned-addresses": [
            [1, "2024-07-22 09:06:58.140438"],
            [0, "2024-07-05 20:44:54.230608"],
            [1, "2024-07-05 09:15:05.626594"],
        ],
        "subnet[1].declined-addresses": [[0, "2024-07-03 16:13:59.401071"]],
        "subnet[1].total-addresses": [[239, "2024-07-03 16:13:59.401058"]],
        "subnet[2].assigned-addresses": [
            [1, "2024-07-22 09:06:58.140439"],
            [1, "2024-07-05 20:44:54.230609"],
            [2, "2024-07-05 09:15:05.626595"],
        ],
        "subnet[2].declined-addresses": [[1, "2024-07-03 16:13:59.401072"]],
        "subnet[2].total-addresses": [[240, "2024-07-03 16:13:59.401059"]],
        "subnet[3].assigned-addresses": [
            [4, "2024-07-22 09:06:58.140439"],
            [5, "2024-07-05 20:44:54.230609"],
        ],
        "subnet[3].declined-addresses": [[0, "2024-07-03 16:13:59.401072"]],
        "subnet[3].total-addresses": [[241, "2024-07-03 16:13:59.401059"]],
        "subnet[4].assigned-addresses": [
            [1, "2024-07-22 09:06:58.140439"],
            [1, "2024-07-05 20:44:54.230609"],
        ],
        "subnet[4].declined-addresses": [[1, "2024-07-03 16:13:59.401072"]],
        "subnet[4].total-addresses": [[242, "2024-07-03 16:13:59.401059"]],
        "subnet[5].assigned-addresses": [
            [1, "2024-07-22 09:06:58.140439"],
            [1, "2024-07-05 20:44:54.230609"],
        ],
        "subnet[5].declined-addresses": [[1, "2024-07-03 16:13:59.401072"]],
        "subnet[5].total-addresses": [[243, "2024-07-03 16:13:59.401059"]],
    }

    expected_metrics = [
        DhcpMetric(
            datetime.fromisoformat("2024-07-22T09:06:58.140438+00:00"),
            IP("2001:db8:1:1::/64"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-05T20:44:54.230608+00:00"),
            IP("2001:db8:1:1::/64"),
            DhcpMetricKey.ASSIGNED,
            0,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-05T09:15:05.626594+00:00"),
            IP("2001:db8:1:1::/64"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-03T16:13:59.401058+00:00"),
            IP("2001:db8:1:1::/64"),
            DhcpMetricKey.TOTAL,
            239,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-22T09:06:58.140439+00:00"),
            IP("2001:db8:1:2::/64"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-05T20:44:54.230609+00:00"),
            IP("2001:db8:1:2::/64"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-05T09:15:05.626595+00:00"),
            IP("2001:db8:1:2::/64"),
            DhcpMetricKey.ASSIGNED,
            2,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-03T16:13:59.401059+00:00"),
            IP("2001:db8:1:2::/64"),
            DhcpMetricKey.TOTAL,
            240,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-22T09:06:58.140439+00:00"),
            IP("2001:db8:1:3::/64"),
            DhcpMetricKey.ASSIGNED,
            4,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-05T20:44:54.230609+00:00"),
            IP("2001:db8:1:3::/64"),
            DhcpMetricKey.ASSIGNED,
            5,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-03T16:13:59.401059+00:00"),
            IP("2001:db8:1:3::/64"),
            DhcpMetricKey.TOTAL,
            241,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-22T09:06:58.140439+00:00"),
            IP("2001:db8:1:4::/64"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-05T20:44:54.230609+00:00"),
            IP("2001:db8:1:4::/64"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-03T16:13:59.401059+00:00"),
            IP("2001:db8:1:4::/64"),
            DhcpMetricKey.TOTAL,
            242,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-22T09:06:58.140439+00:00"),
            IP("2001:db8:1:5::/64"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-05T20:44:54.230609+00:00"),
            IP("2001:db8:1:5::/64"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-03T16:13:59.401059+00:00"),
            IP("2001:db8:1:5::/64"),
            DhcpMetricKey.TOTAL,
            243,
        ),
    ]

    return config, statistics, expected_metrics


@pytest.fixture
def valid_dhcp4():
    config = {
        "Dhcp4": {
            "valid-lifetime": 4000,
            "renew-timer": 1000,
            "rebind-timer": 2000,
            "preferred-lifetime": 3000,
            "interfaces-config": {"interfaces": ["eth0"]},
            "lease-database": {
                "type": "memfile",
                "persist": True,
                "name": "/var/lib/kea/dhcp6.leases",
            },
            "subnet4": [
                {
                    "id": 1,
                    "subnet": "192.0.1.0/24",
                    "pools": [{"pool": "192.0.1.1-192.0.1.10"}],
                },
                {
                    "id": 2,
                    "subnet": "192.0.2.0/24",
                    "pools": [
                        {"pool": "192.0.2.1-192.0.2.10"},
                        {"pool": "192.0.2.128/25"},
                    ],
                },
            ],
            "shared-networks": [
                {
                    "name": "shared-network-1",
                    "subnet4": [
                        {
                            "id": 3,
                            "subnet": "192.0.3.0/24",
                        },
                        {
                            "id": 4,
                            "subnet": "192.0.4.0/24",
                        },
                    ],
                },
                {
                    "name": "shared-network-2",
                    "subnet4": [
                        {
                            "id": 5,
                            "subnet": "192.0.5.0/24",
                        }
                    ],
                },
            ],
        }
    }
    statistics = {
        "subnet[1].assigned-addresses": [
            [1, "2024-07-22 09:06:58.140438"],
            [0, "2024-07-05 20:44:54.230608"],
            [1, "2024-07-05 09:15:05.626594"],
        ],
        "subnet[1].declined-addresses": [[0, "2024-07-03 16:13:59.401071"]],
        "subnet[1].total-addresses": [[239, "2024-07-03 16:13:59.401058"]],
        "subnet[2].assigned-addresses": [
            [1, "2024-07-22 09:06:58.140439"],
            [1, "2024-07-05 20:44:54.230609"],
            [2, "2024-07-05 09:15:05.626595"],
        ],
        "subnet[2].declined-addresses": [[1, "2024-07-03 16:13:59.401072"]],
        "subnet[2].total-addresses": [[240, "2024-07-03 16:13:59.401059"]],
        "subnet[3].assigned-addresses": [
            [4, "2024-07-22 09:06:58.140439"],
            [5, "2024-07-05 20:44:54.230609"],
        ],
        "subnet[3].declined-addresses": [[0, "2024-07-03 16:13:59.401072"]],
        "subnet[3].total-addresses": [[241, "2024-07-03 16:13:59.401059"]],
        "subnet[4].assigned-addresses": [
            [1, "2024-07-22 09:06:58.140439"],
            [1, "2024-07-05 20:44:54.230609"],
        ],
        "subnet[4].declined-addresses": [[1, "2024-07-03 16:13:59.401072"]],
        "subnet[4].total-addresses": [[242, "2024-07-03 16:13:59.401059"]],
        "subnet[5].assigned-addresses": [
            [1, "2024-07-22 09:06:58.140439"],
            [1, "2024-07-05 20:44:54.230609"],
        ],
        "subnet[5].declined-addresses": [[1, "2024-07-03 16:13:59.401072"]],
        "subnet[5].total-addresses": [[243, "2024-07-03 16:13:59.401059"]],
    }

    expected_metrics = [
        DhcpMetric(
            datetime.fromisoformat("2024-07-22T09:06:58.140438+00:00"),
            IP("192.0.1.0/24"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-05T20:44:54.230608+00:00"),
            IP("192.0.1.0/24"),
            DhcpMetricKey.ASSIGNED,
            0,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-05T09:15:05.626594+00:00"),
            IP("192.0.1.0/24"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-03T16:13:59.401058+00:00"),
            IP("192.0.1.0/24"),
            DhcpMetricKey.TOTAL,
            239,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-22T09:06:58.140439+00:00"),
            IP("192.0.2.0/24"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-05T20:44:54.230609+00:00"),
            IP("192.0.2.0/24"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-05T09:15:05.626595+00:00"),
            IP("192.0.2.0/24"),
            DhcpMetricKey.ASSIGNED,
            2,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-03T16:13:59.401059+00:00"),
            IP("192.0.2.0/24"),
            DhcpMetricKey.TOTAL,
            240,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-22T09:06:58.140439+00:00"),
            IP("192.0.3.0/24"),
            DhcpMetricKey.ASSIGNED,
            4,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-05T20:44:54.230609+00:00"),
            IP("192.0.3.0/24"),
            DhcpMetricKey.ASSIGNED,
            5,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-03T16:13:59.401059+00:00"),
            IP("192.0.3.0/24"),
            DhcpMetricKey.TOTAL,
            241,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-22T09:06:58.140439+00:00"),
            IP("192.0.4.0/24"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-05T20:44:54.230609+00:00"),
            IP("192.0.4.0/24"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-03T16:13:59.401059+00:00"),
            IP("192.0.4.0/24"),
            DhcpMetricKey.TOTAL,
            242,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-22T09:06:58.140439+00:00"),
            IP("192.0.5.0/24"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-05T20:44:54.230609+00:00"),
            IP("192.0.5.0/24"),
            DhcpMetricKey.ASSIGNED,
            1,
        ),
        DhcpMetric(
            datetime.fromisoformat("2024-07-03T16:13:59.401059+00:00"),
            IP("192.0.5.0/24"),
            DhcpMetricKey.TOTAL,
            243,
        ),
    ]

    return config, statistics, expected_metrics


def kearesponse(val, status=KeaStatus.SUCCESS):
    return f'''
[
    {{
        "result": {status},
        "arguments": {json.dumps(val)}
    }}
]
    '''


@pytest.fixture(autouse=True)
def responsequeue(monkeypatch):
    """
    Any test that include this fixture, will automatically mock
    requests.Session.post() and requests.post(). The fixture returns a
    namespace with three functions:

    responsequeue.add() can be used to append text strings or functions that
    return text strings to a fifo queue of post responses that in fifo order
    will be returned as proper requests.Response objects on calls to
    requests.post() and requests.Session().post().

    responsequeue.remove() removes a specific fifo queue.

    responsequeue.clear() can be used to clear the all fifo queues.
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
                text = first(
                    arguments=data.get("arguments", {}), service=data.get("service", [])
                )
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

    def remove_command_responses(command_name):
        command_responses.pop(command_name, None)

    def clear_command_responses():
        command_responses.clear()

    def prefill_command_responses(expected_service, config=None, statistics=None):
        def config_get_response(arguments, service):
            assert service == [
                expected_service
            ], f"KeaDhcpSource for service [{expected_service}] should not send requests to {service}"
            return kearesponse(config)

        def statistic_get_response(arguments, service):
            assert service == [
                expected_service
            ], f"KeaDhcpSource for service [{expected_service}] should not send requests to {service}"
            return kearesponse({arguments["name"]: statistics[arguments["name"]]})

        if config is not None:
            add_command_response("config-get", config_get_response)
        if statistics is not None:
            add_command_response("statistic-get", statistic_get_response)

    class ResponseQueue:
        add = add_command_response
        remove = remove_command_responses
        clear = clear_command_responses
        prefill = prefill_command_responses

    monkeypatch.setattr(requests, 'post', new_post_function)
    monkeypatch.setattr(requests.Session, 'post', new_post_method)

    return ResponseQueue
