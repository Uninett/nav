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
    Communicates with a Kea Control Agent and fetches metrics for each
    subnet managed by the Kea DHCP server serving a specific ip
    version that is controlled by the Kea Control Agent (see
    `KeaDhcpMetricSource.fetch_metrics`).
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
        Returns a list containing the most recent DHCP metrics for
        each subnet managed by the Kea DHCP server. For each subnet
        and DhcpMetric-key combination, there is at least one
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
        metric_keys = (
            ("total-addresses", DhcpMetricKey.TOTAL),
            ("assigned-addresses", DhcpMetricKey.ASSIGNED),
        )
        metrics = []

        with requests.Session() as s:
            config = self._fetch_config(s)
            subnets = _subnets_of_config(config, self.dhcp_version)
            for subnet_id, netprefix in subnets:
                for kea_key, nav_key in metric_keys:
                    kea_name = f"subnet[{subnet_id}].{kea_key}"
                    try:
                        response = self._send_query(s, "statistic-get", name=kea_name)
                    except KeaEmpty:
                        continue
                    timeseries = response.get("arguments", {}).get(kea_name, [])
                    if len(timeseries) == 0:
                        _logger.error(
                            "fetch_metrics: Could not fetch metric '%r' for subnet "
                            "'%s' from Kea: '%s' from Kea is an empty list.",
                            nav_key,
                            netprefix,
                            kea_name,
                        )
                    for value, timestring in timeseries:
                        metric = DhcpMetric(
                            self._parsetime(timestring), netprefix, nav_key, value
                        )
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
        Control Agent controls.
        """
        if (
            self.dhcp_config is None
            or (dhcp_confighash := self.dhcp_config.get("hash", None)) is None
            or self._fetch_config_hash(session) != dhcp_confighash
        ):
            response = self._send_query(session, "config-get")
            try:
                self.dhcp_config = response["arguments"][f"Dhcp{self.dhcp_version}"]
            except KeyError as err:
                raise KeaException(
                    "Unrecognizable response to the 'config-get' request",
                    {"Response": response}
                ) from err
        return self.dhcp_config

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
        post_data = json.dumps(
            {
                "command": command,
                "arguments": {**kwargs},
                "service": [f"dhcp{self.dhcp_version}"],
            }
        )
        request_summary = {
            "Description": f"Sending request to Kea Control Agent at {self.rest_uri}",
            "Status": "sending",
            "Location": self.rest_uri,
            "Request": post_data,
        }

        _logger.debug(request_summary)

        request_summary["Validity"] = "Invalid Kea response"
        try:
            responses = session.post(
                self.rest_uri,
                data=post_data,
                timeout=self.timeout,
            )
            request_summary["Status"] = "complete"
            request_summary["Response"] = responses.text
            request_summary["HTTP Status"] = responses.status_code
            responses = responses.json()
        except JSONDecodeError as err:
            raise KeaException(
                "Server does not look like a Kea Control Agent; "
                "expected response content to be JSON",
                request_summary
            ) from err
        except RequestException as err:
            raise KeaException(
                "HTTP-related error during request to server",
                request_summary
            ) from err

        if not isinstance(responses, list):
            # See https://kea.readthedocs.io/en/kea-2.6.0/arm/ctrl-channel.html#control-agent-command-response-format
            raise KeaException(
                "Invalid response; server has likely rejected a query",
                request_summary
            )
        if not (len(responses) == 1 and "result" in responses[0]):
            # We've only sent the command to *one* service. Thus responses should contain *one* response.
            raise KeaException(
                "Server does not look like a Kea Control Agent; "
                "expected response content to be a JSON list "
                "of a single object that has 'result' as one of its keys. ",
                request_summary
            )
        request_summary["Validity"] = "Valid Kea response"

        _logger.debug(request_summary)

        response = responses[0]
        status = response["result"]

        if status == KeaStatus.SUCCESS:
            return response
        elif status == KeaStatus.UNSUPPORTED:
            raise KeaUnsupported(
                "Command '{command}' not supported by Kea",
                request_summary
            )
        elif status == KeaStatus.EMPTY:
            raise KeaEmpty(
                "Requested resource not found",
                request_summary
            )
        elif status == KeaStatus.ERROR:
            raise KeaError(
                "Kea failed during command processing",
                request_summary
            )
        elif status == KeaStatus.CONFLICT:
            raise KeaConflict(
                "Kea failed apply requested changes",
                request_summary
            )
        raise KeaError(
            "Kea returned an unkown status response",
            request_summary
        )
        

    def _parsetime(self, timestamp: str) -> int:
        """Parse the timestamp string used in Kea's timeseries into unix time"""
        fmt = "%Y-%m-%d %H:%M:%S.%f"
        return datetime.strptime(timestamp, fmt).replace(tzinfo=self.tzinfo)


def _subnets_of_config(config: dict, ip_version: int) -> list[tuple[int, IP]]:
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
        id = subnet.get("id", None)
        prefix = subnet.get("subnet", None)
        if id is None or prefix is None:
            _logger.warning(
                "id or prefix missing from a subnet's configuration: %r",
                subnet
            )
            continue
        subnets.append((id, IP(prefix)))
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
            details = "".join(f"\n{label}: {info}" for label, info in self.details)
        return "".join(doc, message, details)

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
