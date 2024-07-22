from IPy import IP
from typing import Iterator, Optional
from itertools import chain
from nav.dhcp.generic_metrics import DhcpMetricSource
from nav.errors import GeneralException
from nav.dhcp.generic_metrics import DhcpMetric, DhcpMetricKey, DhcpMetricSource
import logging
from requests import RequestException, JSONDecodeError
import requests
import calendar
import time
import json
from enum import IntEnum

_logger = logging.getLogger(__name__)

class KeaDhcpMetricSource(DhcpMetricSource):
    """
    Sends http requests to Kea Control Agent on `self.rest_uri` to fetch metrics
    from all subnets managed by the Kea DHCP server (serving ip version
    `dhcp_version` addresses) that the Kea Control Agent controls.
    """
    def __init__(
            self,
            address: str,
            port: int,
            *args,
            https: bool = True,
            dhcp_version: int = 4,
            timeout = 10,
            **kwargs,
    ):
        """
        Instantiate a KeaDhcpMetricSource that fetches information via the Kea
        Control Agent listening to `port` on `address`.
        """
        super(*args, **kwargs)
        scheme = "https" if https else "http"
        self.rest_uri = f"{scheme}://{address}:{port}/"
        self.dhcp_version = dhcp_version
        self.dhcp_config: Optional[dict] = None

    def fetch_metrics(self) -> Iterator[DhcpMetric]:
        """
        Fetch total addresses, assigned addresses, and declined addresses of all
        subnets the Kea DHCP server serving ip version `dhcp_version` maintains.
        """

        metric_keys = (
            ("total-addresses", DhcpMetricKey.MAX),
            ("assigned-addresses", DhcpMetricKey.CUR),
            ("declined-addresses", DhcpMetricKey.TOUCH),
        )
        metrics = []

        with requests.Session as s:
            config = self._fetch_config(s)
            subnets = _subnets_of_config(config, self.dhcp_version)
            for subnetid, prefix in subnets:
                for kea_key, nav_key in metric_keys:
                    kea_statisticname = f"subnet[{subnetid}].{kea_key}"
                    response = self._send_query(s, "statistic-get", name=kea_statisticname)
                    timeseries = response.get("arguments", {}).get(kea_statisticname, [])
                    if len(timeseries) == 0:
                        _logger.error(
                            "fetch_metrics: Could not fetch metric '%r' for subnet "
                            "'%s' from Kea: '%s' from Kea is an empty list.",
                            nav_key, prefix, kea_statisticname,
                        )
                    for value, timestamp in timeseries:
                        metrics.append(
                            DhcpMetric(_parsetime(timestamp), prefix, nav_key, value)
                        )

        if sorted(subnets) != sorted(_subnets_of_config(self._fetch_config())):
            _logger.error(
                "Subnet configuration was modified during metric fetching, "
                "this may cause metric data being associated with wrong "
                "subnet in some rare cases."
            )

        return metrics


    def _fetch_config(self, session: requests.Session) -> dict:
        """
        Fetch the current config of the Kea DHCP server serving ip version
        `dhcp_version`
        """
        if (
            self.dhcp_config is None
            or (dhcp_confighash := self.dhcp_config.get("hash", None)) is None
            or self._fetch_config_hash(session) != dhcp_confighash
        ):
            self.dhcp_config = self._send_query(session, "config-get").get("arguments", {}).get(f"Dhcp{self.dhcp_version}", None)
            if self.dhcp_config is None:
                raise KeaError(
                    "Could not fetch configuration of Kea DHCP server from Kea Control "
                    f"Agent at {self.rest_uri}"
                )

        return self.dhcp_config


    def _fetch_config_hash(self, session: requests.Session) -> Optional[str]:
        """
        Fetch the hash of the current config of the Kea DHCP server serving ip
        version `dhcp_version`
        """
        return self._send_query(session, "config-hash-get").get("arguments", {}).get("hash", None)


    def _send_query(self, session: requests.Session, command: str, **kwargs) -> dict:
        """
        Send `command` to the Kea Control Agent. An exception is raised iff
        there was an HTTP related error while sending `command` or a response
        does not look like it is coming from a Kea Control Agent. All raised
        exceptions are of type `KeaError`. Proper error responses as documented
        in the API are logged but results in an empty dictionary being returned.
        """
        postdata = json.dumps({
            "command": command,
            "arguments": **kwargs,
            "service": [f"dhcp{self.dhcp_version}"]
        })
        _logger.info(
            "send_query: Post request to Kea Control Agent at %s with data %s",
            self.rest_uri,
            postdata,
        )
        try:
            responses = session.post(
                self.rest_uri,
                data=postdata,
                headers=self.rest_headers,
                timeout=self.timeout,
            )
            responses = responses.json()
        except RequestException as err:
            raise KeaError(
                f"HTTP related error when requesting Kea Control Agent at {self.rest_uri}",
            ) from err
        except JSONDecodeError as err:
            raise KeaError(
                f"Uri {self.rest_uri} most likely not pointing at a Kea "
                f"Control Agent (expected json, responded with: {responses!r})",
            ) from err
        if not isinstance(responses, list):
            # See https://kea.readthedocs.io/en/kea-2.6.0/arm/ctrl-channel.html#control-agent-command-response-format
            raise KeaError(
                f"Kea Control Agent at {self.rest_uri} have likely rejected "
                f"a query (responded with: {responses!r})"
            )
        if not (len(responses) == 1 and "result" in responses[0]):
            # "We've only sent the command to *one* service. Thus responses should contain *one* response."
            raise KeaError(
                f"Uri {self.rest_uri} most likely not pointing at a Kea "
                "Control Agent (expected json list with one object having "
                f"key 'result', responded with: {responses!r})",
            )
        response = responses[0]
        if response["result"] == KeaStatus.SUCCESS:
            return response
        else:
            _logger.error(
                "send_query: Kea at %s did not succeed fulfilling query %s "
                "(responded with: %r) ",
                self.rest_uri,
                postdata,
                responses
            )
            return {}

def _parsetime(timestamp: str) -> int:
    """Parse the timestamp string used in Kea's timeseries into unix time"""
    return calendar.timegm(time.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f"))

def _subnets_of_config(config: dict, ip_version: int) -> Iterator[tuple[int, IP]]:
    """
    List the id and prefix of subnets listed in the Kea DHCP configuration
    `config`
    """
    subnetkey = f"subnet{ip_version}"
    for subnet in chain.from_iterable(
            [config.get(subnetkey, [])]
            + [network.get(subnetkey, []) for network in config.get("shared-networks", [])]
    ):
        id = subnet.get("id", None)
        prefix = subnet.get("subnet", None)
        if id is None or prefix is None:
            _logger.warning("subnets: id or prefix missing from a subnet's configuration: %r", subnet)
            continue
        yield id, IP(prefix)


class KeaError(GeneralException):
    """Error related to interaction with a Kea Control Agent"""

class KeaStatus(IntEnum):
    """Status of a response sent from a Kea Control Agent."""
    # Successful operation.
    SUCCESS = 0
    # General failure.
    ERROR = 1
    # Command is not supported.
    UNSUPPORTED = 2
    # Successful operation, but failed to produce any results.
    EMPTY = 3
    # Unsuccessful operation due to a conflict between the command arguments and the server state.
    CONFLICT = 4
