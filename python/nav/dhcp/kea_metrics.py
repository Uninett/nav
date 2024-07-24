from IPy import IP
from typing import Optional
from itertools import chain
from nav.dhcp.generic_metrics import DhcpMetricSource
from nav.errors import GeneralException
from nav.dhcp.generic_metrics import DhcpMetric, DhcpMetricKey, DhcpMetricSource
from datetime import datetime
import logging
from requests import RequestException, JSONDecodeError
import requests
import json
from enum import IntEnum

_logger = logging.getLogger(__name__)


class KeaDhcpMetricSource(DhcpMetricSource):
    """
    Communicates with a Kea Control Agent and fetches metrics from all
    subnets managed by the Kea DHCP server serving a specific ip
    version that is controlled the Kea Control Agent.
    """

    def __init__(
        self,
        address: str,
        port: int,
        *args,
        https: bool = True,
        dhcp_version: int = 4,
        timeout: int = 10,
        tzinfo: datetime.tzinfo = datetime.now().astimezone().tzinfo,
        **kwargs,
    ):
        """
        Returns a KeaDhcpMetricSource that fetches DHCP metrics via
        the Kea Control Agent listening to `port` on `address`.

        :param https:        if True, use https. Otherwise, use http
        :param dhcp_version: ip version served by Kea DHCP server
        :param timeout:      how long to wait for a http response from
                             the Kea Control Agent before timing out
        :param tzinfo:       the timezone of the Kea Control Agent.
        """
        super(*args, **kwargs)
        scheme = "https" if https else "http"
        self.rest_uri = f"{scheme}://{address}:{port}/"
        self.dhcp_version = dhcp_version
        self.dhcp_config: Optional[dict] = None
        self.timeout = timeout
        self.tzinfo = tzinfo

    def fetch_metrics(self) -> list[DhcpMetric]:
        """
        Returns a list of DHCP metrics. For each subnet and
        DhcpMetric-key combination, there is at least one
        corresponding metric in the returned list if no errors occur.

        If the Kea Control Agent responds with an empty response to
        one or more of the requests for some metric(s), these metrics
        will be missing in the returned list, but a list is still
        succesfully returned. Other errors while requesting metrics
        will cause a fitting subclass of KeaException to be raised:

        Communication errors (HTTP errors, JSON errors, access control
        errors) causes a KeaException that is reraised from the
        specific communication error to be raised.

        If the Kea Control Agent doesn't support the 'config-get' and
        'statistic-get' commands, then a KeaUnsupported exception is
        raised.

        General errors reported by the Kea Control Agent causes a
        KeaError to be raised.
        """
        metrics = []

        with requests.Session() as s:
            config = self._fetch_config(s)
            subnets = _subnets_of_config(config, self.dhcp_version)
            for subnetid, netprefix in subnets:
                for kea_key, nav_key in metric_keys:
                    kea_name = f"subnet[{subnetid}].{kea_key}"
                    response = self._send_query(s, "statistic-get", name=kea_name)
                    timeseries = response.get("arguments", {}).get(kea_name, [])
                    if len(timeseries) == 0:
                        _logger.error(
                            "fetch_metrics: Could not fetch metric '%r' for subnet "
                            "'%s' from Kea: '%s' from Kea is an empty list.",
                            nav_key,
                            netprefix,
                            kea_name,
                        )
                    for val, t in timeseries:
                        metric = DhcpMetric(self._parsetime(t), netprefix, nav_key, val)
                        metrics.append(metric)

        newsubnets = _subnets_of_config(self._fetch_config(s), self.dhcp_version)
        if sorted(subnets) != sorted(newsubnets):
            _logger.error(
                "Subnet configuration was modified during metric fetching, "
                "this may cause metric data being associated with wrong "
                "subnet in some rare cases."
            )

        return metrics

    def _fetch_config(self, session: requests.Session) -> dict:
        """
        Returns the current config of the Kea DHCP server that the Kea
        Control Agent controls
        """
        if (
            self.dhcp_config is None
            or (dhcp_confighash := self.dhcp_config.get("hash", None)) is None
            or self._fetch_config_hash(session) != dhcp_confighash
        ):
            response = self._send_query(session, "config-get")
            status = response.get("result", KeaStatus.ERROR)
            arguments = response.get("arguments", {})
            self.dhcp_config = arguments.get(f"Dhcp{self.dhcp_version}", None)
            if self.dhcp_config is None or status != KeaStatus.SUCCESS:
                raise KeaError(
                    "Could not fetch configuration of Kea DHCP server from Kea Control "
                    f"Agent at {self.rest_uri}"
                )
        return self.dhcp_config

    def _fetch_config_hash(self, session: requests.Session) -> Optional[str]:
        """
        Returns the hash of the current config of the Kea DHCP server
        that the Kea Control Agent controls
        """
        return (
            self._send_query(session, "config-hash-get")
            .get("arguments", {})
            .get("hash", None)
        )

    def _send_query(self, session: requests.Session, command: str, **kwargs) -> dict:
        """
        Returns the response from the Kea Control Agent to the query
        with command `command`. Additional keyword arguments to this
        function will be passed as arguments to the command.

        Communication errors (HTTP errors, JSON errors, access control
        errors, unrecognized json response formats) causes a
        KeaException to be raised. If possible, it is reraised from a
        more descriptive error such as a HTTPError.

        Valid Kea Control Agent responses that indicate a failure on
        the server-end causes a descriptive subclass of KeaException
        to be raised.
        """
        postdata = json.dumps(
            {
                "command": command,
                "arguments": {**kwargs},
                "service": [f"dhcp{self.dhcp_version}"],
            }
        )
        _logger.info(
            "send_query: Post request to Kea Control Agent at %s with data %s",
            self.rest_uri,
            postdata,
        )
        try:
            responses = session.post(
                self.rest_uri,
                data=postdata,
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
                responses,
            )
            return {}

    def _parsetime(self, timestamp: str) -> int:
        """Parse the timestamp string used in Kea's timeseries into unix time"""
        fmt = "%Y-%m-%d %H:%M:%S.%f"
        return datetime.strptime(timestamp, fmt).replace(tzinfo=self.tzinfo)


def _subnets_of_config(config: dict, ip_version: int) -> list[tuple[int, IP]]:
    """
    List the id and prefix of subnets listed in the Kea DHCP
    configuration `config`
    """
    subnets = []
    subnetkey = f"subnet{ip_version}"
    for subnet in chain.from_iterable(
        [config.get(subnetkey, [])]
        + [network.get(subnetkey, []) for network in config.get("shared-networks", [])]
    ):
        id = subnet.get("id", None)
        prefix = subnet.get("subnet", None)
        if id is None or prefix is None:
            msg = "subnets: id or prefix missing from a subnet's configuration: %r"
            _logger.warning(msg, subnet)
            continue
        subnets.append((id, IP(prefix)))
    return subnets


class KeaError(GeneralException):
    """Error related to interaction with a Kea Control Agent"""


class KeaStatus(IntEnum):
    """Status of a response sent from a Kea Control Agent."""
    SUCCESS = 0
    ERROR = 1
    UNSUPPORTED = 2
    EMPTY = 3
    CONFLICT = 4
