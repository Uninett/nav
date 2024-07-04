from IPy import IP
from typing import Iterator, Optional
from itertools import chain
from nav.dhcp.generic_metrics import DhcpMetricSource
from nav.errors import GeneralException
import logging

logger = logging.getLogger(__name__)

class KeaDhcpMetricSource(DhcpMetricSource):
    dhcp_config: dict
    dhcp_confighash: Optional[str]
    dhcp_version: int
    rest_url: str

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
        super(*args, **kwargs)
        scheme = "https" if https else "http"
        self.rest_url = f"{scheme}://{address}:{port}/"
        self.dhcp_version = dhcp_version
        self.dchp_confighash = None

    def fetch_metrics(self) -> Iterator[DhcpMetric]:
        config = self.fetch_config()

        metrics = []
        with requests.Session as s:
            for subnetid, prefix in subnets_of_config(config):
                for kea_key, nav_key in (
                        ("total-addresses", DhcpMetricKey.MAX),
                        ("assigned-addresses", DhcpMetricKey.CUR),
                        ("declined-addresses", DhcpMetricKey.TOUCH),
                ):
                    kea_statisticname = f"subnet[{subnetid}].{kea_key}"
                    response = self.send_query(session, "statistic-get", name=kea_statisticname)
                    timeseries = response.get("arguments", {}).get(kea_statisticname, [])
                    if len(timeseries) == 0:
                        logger.error(
                            "fetch_metrics: Could not fetch metric '%r' for subnet "
                            "'%s' from Kea: '%s' from Kea is an empty list.",
                            nav_key, prefix, kea_statisticname,
                        )
                        continue
                    for value, timestamp in timeseries:
                        metrics.append(
                            DhcpMetric(parsetime(timestamp), prefix, nav_key, value)
                        )

        if sorted(subnets_of_config(config)) != sorted(subnets_of_config(self.fetch_config())):
            logger.error(
                "Subnet configuration was modified during metric fetching, "
                "this may cause metric data being associated with wrong "
                "subnet."
            )
            
        return metrics

    def self.send_query(self, session, command, **kwargs) -> dict:
        postdata = json.dumps({
            "command": command,
            "arguments": **kwargs,
            "service": [f"dhcp{dhcp_version}"]
        })
        logger.info("send_query: Post request to Kea with data %s", postdata)
        r = session.post(
            self.rest_url,
            data=postdata,
            headers=self.rest_headers,
            timeout=timeout,
        )
        rjson = r.json()
        if not isinstance(rjson, list):
            # See https://kea.readthedocs.io/en/kea-2.6.0/arm/ctrl-channel.html#control-agent-command-response-format
            raise KeaError(
                "send_query: Kea have likely rejected a query (responsed with: {rjson!r})"
            )
        assert len(rjson) == 1
        response = rjson.pop()
        if response.get("result", KeaStatus.ERROR) == KeaStatus.SUCCESS
            return response
        else:
            logger.error("send_query: Kea did not succeed fulfilling a query (responded with: {rjson!r}) ")
            return {}

def parsetime(timestamp: str) -> int:
    return calendar.timegm(time.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f"))
                    
def subnets_of_config(config: dict) -> Iterator[tuple[int, IP]]:
    if "Dhcp4" in config:
        dhcpversion = 4
        config = config["Dhcp4"]
        subnetkey = "subnet4"
    elif "Dhcp6" in config:
        dhcpversion = 6
        config = config["Dhcp6"]
        subnetkey = "subnet6"
    else:
        logger.warning("subnets: expected a Kea Dhcp4 or Kea Dhcp6 config, got: ", config)
        return

    for subnet in chain.from_iterable(
            [config.get(subnetkey, [])]
            + [network.get(subnetkey, []) for network in config.get("shared-networks", [])]
    ):
        id = subnet.get("id", None)
        prefix = subnet.get("subnet", None)
        if id is None or prefix is None:
            logger.warning("subnets: id or prefix missing from a subnet's configuration: %r", subnet)
            continue
        yield id, IP(prefix)

###>
d = {"Dhcp4": {}}
d = {"Dhcp4": {"subnet4": []}}
d = {"Dhcp4": {"subnet4": [{"subnet": "192.0.2.0/24", "id": 1}]}}
d = {"Dhcp4": {"subnet4": [{"subnet": "192.0.2.0/24", "id": 1}, {"subnet": "10.1.0.0/16", "id": 2}]}}
d = {"Dhcp4": {"subnet4": [{"subnet": "192.0.2.0/24", "id": 1}, {"subnet": "10.1.0.0/16", "id": 2}, {"subnet": "10.2.0.0/17", "id": 3}]}}
d = {"Dhcp4": {
    "subnet4": [{"subnet": "192.0.2.0/24", "id": 1}, {"subnet": "10.1.0.0/16", "id": 2}, {"subnet": "10.2.0.0/17", "id": 3}],
    "shared-networks": []}}
d = {"Dhcp4": {
    "shared-networks": [{"subnet4": [{"subnet": "192.0.3.0/25", "id": 4}, {"subnet": "192.0.4.0/29", "id": 5}]}]}}
d = {"Dhcp4": {
    "subnet4": [{"subnet": "192.0.2.0/24", "id": 1}, {"subnet": "10.1.0.0/16", "id": 2}, {"subnet": "10.2.0.0/17", "id": 3}],
    "shared-networks": [{"subnet4": [{"subnet": "192.0.3.0/25", "id": 4}, {"subnet": "192.0.4.0/29", "id": 5}]}]}}

for subnet in subnets_of_config(d):
    print(repr(subnet))
###<

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
