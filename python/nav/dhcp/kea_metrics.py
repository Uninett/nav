"""
Exports the KeaDhcpMetricSource class for fetching DHCP metrics from
Kea DHCP servers
                            |
             Managed by NAV | Managed externally
                            |
                       HTTP |                       IPC
KeaDhcpMetricSource <---------> Kea Control Agent <=====> Kea DHCP4 server/Kea DHCP6 server
                            |
                            |
"""
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

_SubnetTuple = tuple[int, IP]  # (subnet_id, netprefix)

class KeaDhcpMetricSource(DhcpMetricSource):
    """
    Communicates with a Kea Control Agent to enable fetching of DHCP
    metrics for each subnet managed by some specific underlying Kea
    DHCP4 or Kea DHCP6 server.

    The sole purpose of this class is to implement the superclass's
    fetch_metrics() method. Public methods are:

    * fetch_metrics(): Fetches DHCP metrics for each subnet managed by
      the Kea DHCP server. Metrics are returned as a list.

    * fetch_metrics_to_graphite(): Inherited from superclass. Fetches
    DHCP metrics as above and sends these to a graphite server.
    """

    def __init__(
        self,
        address: str,
        port: int,
        https: bool = True,
        dhcp_version: int = 4,
        timeout: int = 10,
        tzinfo: datetime.tzinfo = None,
    ):
        """
        Instantiate a KeaDhcpMetricSource that fetches DHCP metrics
        from the Kea DHCP server managing IP version `dhcp_version`
        addresses, whose metrics is reachable via the Kea Control
        Agent listening to `port` on `address`.

        :param address:      IP address of the Kea Control Agent
        :param port:         TCP port of the Kea Control Agent
        :param https:        if True, use https. Otherwise, use http
        :param dhcp_version: ip version served by Kea DHCP server
        :param timeout:      how long to wait for a http response from
                             the Kea Control Agent before timing out
        :param tzinfo:       the timezone of the Kea Control Agent.
        """
        super()
        scheme = "https" if https else "http"
        self._rest_uri = f"{scheme}://{address}:{port}/"
        self._dhcp_version = dhcp_version
        self._dhcp_config: Optional[dict] = None
        self._timeout = timeout
        self._tzinfo = tzinfo or datetime.now().astimezone().tzinfo

    def fetch_metrics(self) -> list[DhcpMetric]:
        """
        Fetches and returns a list containing the most recent DHCP
        metrics for each subnet managed by the Kea DHCP server. For
        each subnet and DhcpMetric-key combination, there is at least
        one corresponding metric in the returned list if no errors
        occur.

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

        with requests.Session() as session:
            config = self._fetch_config(session)
            subnets = _subnets_of_config(config, self._dhcp_version)

            for subnet in subnets:
                subnet_metrics = self._fetch_subnet_metrics(subnet, session)
                metrics.extend(subnet_metrics)

            newest_subnets = _subnets_of_config(self._fetch_config(session), self._dhcp_version)
            if sorted(subnets) != sorted(newest_subnets):
                _logger.warning(
                    "Subnet configuration was modified during DHCP metric fetching, "
                    "this may cause metric data being associated with wrong subnet."
                )

        return metrics


    def _fetch_subnet_metrics(
            self, subnet: _SubnetTuple, session: requests.Session
    ) -> list[DhcpMetric]:
        metric_keys = (
            ("total-addresses", DhcpMetricKey.TOTAL),
            ("assigned-addresses", DhcpMetricKey.ASSIGNED),
        )
        metrics = []

        for kea_key, nav_key in metric_keys:
            kea_name = f"subnet[{subnet_id}].{kea_key}"
            try:
                response = self._send_query(session, "statistic-get", name=kea_name)
            except KeaEmpty:
                continue
            timeseries = response.get("arguments", {}).get(kea_name, [])
            if len(timeseries) == 0:
                _logger.warning(
                    "Could not fetch metric '%r' for subnet '%s' from Kea: '%s' from Kea "
                    "is an empty list.",
                    nav_key,
                    netprefix,
                    kea_name,
                )
            for value, timestring in timeseries:
                metric = DhcpMetric(
                    self._parsetime(timestring), netprefix, nav_key, value
                )
                metrics.append(metric)

        return metrics


    def _fetch_config(self, session: requests.Session) -> dict:
        """
        Returns the current config of the Kea DHCP server that the Kea
        Control Agent controls.
        """
        if (
            self._dhcp_config is None
            or (dhcp_confighash := self._dhcp_config.get("hash", None)) is None
            or self._fetch_config_hash(session) != dhcp_confighash
        ):
            response = self._send_query(session, "config-get")
            try:
                self._dhcp_config = response["arguments"][f"Dhcp{self._dhcp_version}"]
            except KeyError as err:
                raise KeaException(
                    "Unrecognizable response to the 'config-get' request",
                    {"Response": response},
                ) from err
        return self._dhcp_config

    def _fetch_config_hash(self, session: requests.Session) -> Optional[str]:
        """
        Returns the hash of the current config of the Kea DHCP server
        that the Kea Control Agent controls.
        """
        try:
            return (
                self._send_query(session, "config-hash-get")
                .get("arguments", {})
                .get("hash", None)
            )
        except KeaUnsupported as err:
            _logger.debug(str(err))
            return None

    def _send_query(self, session: requests.Session, command: str, **kwargs) -> dict:
        """
        Returns the response from the Kea Control Agent to the query
        with command `command` instructed towards the Kea DHCP server.
        Additional keyword arguments to this function will be passed
        as arguments to the command.

        Communication errors (HTTP errors, JSON errors, access control
        errors, unrecognized json response formats) causes a
        KeaException to be raised. If possible, it is reraised from a
        more descriptive error such as an HTTPError.

        Valid Kea Control Agent responses that indicate a failure on
        the server-end causes a descriptive subclass of KeaException
        to be raised.
        """
        request_summary = {
            "Description": f"Sending request to Kea Control Agent at {self._rest_uri}",
            "Status": "sending",
            "Location": self._rest_uri,
            "Command": command,
        }
        _logger.debug(request_summary)

        post_data = json.dumps(
            {
                "command": command,
                "arguments": {**kwargs},
                "service": [f"dhcp{self._dhcp_version}"],
            }
        )
        request_summary["Validity"] = "Invalid Kea response"
        try:
            responses = session.post(
                self._rest_uri,
                data=post_data,
                timeout=self._timeout,
                headers={"Content-Type": "application/json"},
            )
            request_summary["Status"] = "complete"
            request_summary["HTTP Status"] = responses.status_code
            responses.raise_for_status()
            responses = responses.json()
        except JSONDecodeError as err:
            raise KeaException(
                "Server does not look like a Kea Control Agent; "
                "expected response content to be JSON",
                request_summary,
            ) from err
        except RequestException as err:
            raise KeaException(
                "HTTP-related error during request to server", request_summary
            ) from err

        if not isinstance(responses, list):
            # See https://kea.readthedocs.io/en/kea-2.6.0/arm/ctrl-channel.html#control-agent-command-response-format
            raise KeaException(
                "Invalid response; server has likely rejected a query", request_summary
            )
        if not (len(responses) == 1 and "result" in responses[0]):
            # `post-data` queries *one* service. Thus `responses` should contain *one* response.
            raise KeaException(
                "Server does not look like a Kea Control Agent; "
                "expected response content to be a JSON list "
                "of a single object that has 'result' as one of its keys. ",
                request_summary,
            )
        request_summary["Validity"] = "Valid Kea response"

        _logger.debug(request_summary)

        response = responses[0]
        status = response["result"]

        if status == KeaStatus.SUCCESS:
            return response
        elif status == KeaStatus.UNSUPPORTED:
            raise KeaUnsupported(details=request_summary)
        elif status == KeaStatus.EMPTY:
            raise KeaEmpty(details=request_summary)
        elif status == KeaStatus.ERROR:
            raise KeaError(details=request_summary)
        elif status == KeaStatus.CONFLICT:
            raise KeaConflict(details=request_summary)
        raise KeaException("Kea returned an unkown status response", request_summary)

    def _parsetime(self, timestamp: str) -> float:
        """Parse the timestamp string used in Kea's timeseries into unix time"""
        fmt = "%Y-%m-%d %H:%M:%S.%f"
        return datetime.strptime(timestamp, fmt).replace(tzinfo=self._tzinfo).timestamp()


def _subnets_of_config(config: dict, ip_version: int) -> list[_SubnetTuple]:
    """
    Returns a list containing one (subnet-id, subnet-prefix) tuple per
    subnet listed in the Kea DHCP configuration `config`.
    """
    subnets = []
    subnetkey = f"subnet{ip_version}"
    for subnet in chain.from_iterable(
        [config.get(subnetkey, [])]
        + [network.get(subnetkey, []) for network in config.get("shared-networks", [])]
    ):
        subnet_id = subnet.get("id", None)
        netprefix = subnet.get("subnet", None)
        if subnet_id is None or netprefix is None:
            _logger.warning(
                "id or prefix missing from a subnet's configuration: %r", subnet
            )
            continue
        subnets.append((subnet_id, IP(netprefix)))
    return subnets


class KeaException(GeneralException):
    """Error related to interaction with a Kea Control Agent"""

    def __init__(self, message: str = "", details: dict[str, str] = {}):
        self.message = message
        self.details = details

    def __str__(self) -> str:
        doc = self.__doc__
        message = ""
        details = ""
        if self.message:
            message = f": {self.message}"
        if self.details:
            details = "\nDetails:\n"
            details += "\n".join(
                f"{label}: {info}" for label, info in self.details.items()
            )
        return "".join([doc, message, details])


class KeaError(KeaException):
    """Kea failed during command processing"""


class KeaUnsupported(KeaException):
    """Unsupported command"""


class KeaEmpty(KeaException):
    """Requested resource not found"""


class KeaConflict(KeaException):
    """Kea failed to apply requested changes due to conflicts with its server state"""


class KeaStatus(IntEnum):
    """Status of a response sent from a Kea Control Agent"""

    SUCCESS = 0
    ERROR = 1
    UNSUPPORTED = 2
    EMPTY = 3
    CONFLICT = 4
