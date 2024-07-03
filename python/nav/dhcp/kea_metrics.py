"""
Functions for querying the Kea Control Agent for statistics from Kea DHCP
servers.

     RESTful-queries                      IPC
nav <---------------> Kea Control Agent <=====> Kea DHCP4 server / Kea DHCP6 server
        (json)

No additional hook libraries are assumed to be included with the Kea Control
Agent that is queried, meaning this module will be able to gather DHCP
statistics from any Kea Control Agent.

* Stork (https://gitlab.isc.org/isc-projects/stork) is used as a guiding
implementation for interacting with the Kea Control Agent.
* See also the Kea Control Agent documentation. This script assumes Kea versions
>= 2.2.0 are used.  (https://kea.readthedocs.io/en/kea-2.2.0/arm/agent.html).
"""

from __future__ import annotations
import calendar
import json
import logging
import requests
import time
from dataclasses import dataclass, asdict
from enum import IntEnum
from IPy import IP
from nav.dhcp.generic_metrics import DhcpMetricSource, DhcpMetric, DhcpMetricKey
from nav.errors import GeneralException
from requests.exceptions import JSONDecodeError, HTTPError, Timeout
from typing import Optional

logger = logging.getLogger(__name__)


class KeaDhcpMetricSource(DhcpMetricSource):
    """
    Using `send_query()`, this class:
    * Maintains an up-to-date `KeaDhcpConfig` representation of the
      configuration of the Kea DHCP server with ip version
      `self.dhcp_version` reachable via the Kea Control Agent listening
      to port `self.rest_port` on IP addresses `self.rest_address`
    * Queries the Kea Control Agent for statistics about each subnet
      found in the `KeaDhcpConfig` representation and creates an
      iterable of `DhcpMetric` that its superclass uses to fill a
      graphite server with metrics.
    """

    rest_address: str  # IP address of the Kea Control Agent server
    rest_port: int  # Port of the Kea Control Agent server
    rest_https: bool  # If true, communicate with Kea Control Agent using https. If false, use http.

    dhcp_version: int  # The IP version of the Kea DHCP server. The Kea Control Agent uses this to tell if we want information from its IPv6 or IPv4 Kea DHCP server
    kea_dhcp_config: dict  # The configuration, i.e. most static pieces of information, of the Kea DHCP server.

    def __init__(
        self,
        address: str,
        port: int,
        *args,
        https: bool = True,
        dhcp_version: int = 4,
        **kwargs,
    ):
        super(*args, **kwargs)
        self.rest_address = address
        self.rest_port = port
        self.rest_https = https
        self.dchp_version = dhcp_version
        self.kea_dhcp_config = None

    def fetch_metrics(self) -> list[DhcpMetric]:
        """
        Implementation of the superclass method for fetching
        standardised dhcp metrics. This method is used by the
        superclass to feed data into a graphite server.
        """
        metrics = []
        try:
            s = requests.Session()
            self.fetch_and_set_dhcp_config(s)
            for subnet in self.kea_dhcp_config.subnets:
                for statistic_key, metric_key in (
                    ("total-addresses", DhcpMetricKey.MAX),
                    ("assigned-addresses", DhcpMetricKey.CUR),
                    ("declined-addresses", DhcpMetricKey.TOUCH),
                ):  # `statistic_key` is the name of the statistic used by Kea. `metric_key` is the name of the statistic used by NAV.
                    kea_statistic_name = f"subnet[{subnet.id}].{statistic_key}"
                    query = KeaQuery(
                        command="statistic-get",
                        service=[f"dhcp{self.dchp_version}"],
                        arguments={
                            "name": kea_statistic_name,
                        },
                    )
                    response = unwrap(
                        send_query(
                            query,
                            self.rest_address,
                            self.rest_port,
                            self.rest_https,
                            session=s,
                        )
                    )

                    datapoints = response["arguments"].get(kea_statistic_name, [])
                    for value, timestamp in datapoints:
                        epochseconds = calendar.timegm(
                            time.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                        )  # Assumes for now that UTC timestamps are returned by Kea Control Agent; I'll need to read the documentation closer!
                        metrics.append(
                            DhcpMetric(epochseconds, subnet.prefix, metric_key, value)
                        )

            used_config = self.kea_dhcp_config
            self.fetch_and_set_dhcp_config(s)
            if sorted(used_config.subnets) != sorted(self.kea_dhcp_config.subnets):
                logger.warning(
                    "Subnet configuration was modified during metric fetching, "
                    "this may cause metric data being associated with wrong "
                    "subnet."
                )
        except Timeout as err:
            logger.warning(
                "Connection to Kea Control Agent timed before or during metric "
                "fetching. Some metrics may be missing.",
                exc_info=err,
            )
        except Exception as err:
            # More detailed information should be logged by deeper exception handlers at the logging.DEBUG level.
            logger.warning(
                "Exception while fetching metrics from Kea Control Agent. Some "
                "metrics may be missing.",
                exc_info=err,
            )
        finally:
            s.close()

        return metrics

    def fetch_and_set_dhcp_config(self, session=None):
        """
        Fetch the current config used by the Kea DHCP server that
        manages addresses of IP version `self.dhcp_version` from the Kea
        Control Agent listening to `self.rest_port` on
        `self.rest_address`.
        """
        # Check if self.kea_dhcp_config is up to date
        if not (
            self.kea_dhcp_config is None
            or self.kea_dhcp_config.config_hash is None
            or self.fetch_dhcp_config_hash(session=session)
            != self.kea_dhcp_config.config_hash
        ):
            return self.kea_dhcp_config

        # self.kea_dhcp_config is not up to date, fetch new
        query = KeaQuery(
            command="config-get",
            service=[f"dhcp{self.dchp_version}"],
            arguments={},
        )
        response = unwrap(
            send_query(
                query,
                self.rest_address,
                self.rest_port,
                self.rest_https,
                session=session,
            )
        )

        self.kea_dhcp_config = KeaDhcpConfig.from_json(response.arguments)
        return self.kea_dhcp_config

    def fetch_dhcp_config_hash(self, session=None):
        """
        For Kea versions >= 2.4.0, fetch and return a hash of the
        current configuration used by the Kea DHCP server. For Kea
        versions < 2.4.0, return None.
        """
        query = KeaQuery(
            command="config-hash-get",
            service=[f"dhcp{self.dchp_version}"],
            arguments={},
        )
        response = unwrap(
            send_query(
                query,
                self.rest_address,
                self.rest_port,
                self.rest_https,
                session=session,
            ),
            require_success=False,
        )

        if response.result == KeaStatus.UNSUPPORTED:
            logger.debug(
                "Kea DHCP%d server does not support quering for the hash of its config",
                self.dchp_version,
            )
            return None
        elif response.success:
            return response.arguments.get("hash", None)
        else:
            raise KeaError(
                "Unexpected error while querying the hash of config file from DHCP server"
            )


@dataclass
class KeaDhcpSubnet:
    """Class representing information about a subnet managed by a Kea DHCP server."""

    id: int  # either specified in the server config or assigned automatically by the dhcp server
    prefix: IP  # e.g. 192.0.2.1/24
    pools: list[tuple[IP]]  # e.g. [(192.0.2.10, 192.0.2.20), (192.0.2.64, 192.0.2.128)]

    @classmethod
    def from_json(cls, subnet_json: dict):
        """
        Initialize and return a Subnet instance based on json

        :param json: python dictionary that is structured the same way as the
        json object representing a subnet in the Kea DHCP config file.
        Example:
            {
                "id": 0
                "subnet": "192.0.2.0/24",
                "pools": [
                    {
                        "pool": "192.0.2.1 - 192.0.2.100"
                    },
                    {
                        "pool": "192.0.2.128/26"
                    }
                ]
            }
        """
        if "id" not in subnet_json:
            raise KeaError("Expected subnetjson['id'] to exist")
        id = subnet_json["id"]

        if "subnet" not in subnet_json:
            raise KeaError("Expected subnetjson['subnet'] to exist")
        prefix = IP(subnet_json["subnet"])

        pools = []
        for obj in subnet_json.get("pools", []):
            pool = obj["pool"]
            if "-" in pool:  # TODO: Error checking?
                # pool == "x.x.x.x - y.y.y.y"
                start, end = (IP(ip) for ip in pool.split("-"))
            else:
                # pool == "x.x.x.x/nn"
                pool = IP(pool)
                start, end = pool[0], pool[-1]
            pools.append((start, end))

        return cls(
            id=id,
            prefix=prefix,
            pools=pools,
        )


@dataclass
class KeaDhcpConfig:
    """
    Class representing information found in the configuration of a Kea DHCP
    server. Most importantly, this class contains:
    * A list of the subnets managed by the DHCP server
    * The IP version of the DCHP server
    """

    # Used to check if there's a new config on the Kea DHCP server
    config_hash: Optional[str]
    dhcp_version: int
    subnets: list[KeaDhcpSubnet]

    @classmethod
    def from_json(
        cls,
        config_json: dict,
        config_hash: Optional[str] = None,
    ):
        """
        Initialize and return a KeaDhcpConfig instance based on json

        :param json: a dictionary that is structured the same way as a
        Kea DHCP configuration.
        Example:
        {
            "Dhcp4": {
                "shared-networks": [
                     {
                         "name": "test-network",
                         "subnet4": [
                             {
                                 "subnet": "10.0.0.0/8",
                                 "pools": [ { "pool":  "10.0.0.1 - 10.0.0.99" } ],
                             },
                             {
                                 "subnet": "192.0.3.0/24",
                                 "pools": [ { "pool":  "192.0.3.100 - 192.0.3.199" } ]
                             }
                         ],
                     }
                 ], # end of shared-networks
                "subnet4": [{
                "id": 1,
                "subnet": "192.0.2.0/24",
                "pools": [
                    {
                        "pool": "192.0.2.1 - 192.0.2.200",
                    },
                ],
                }] # end of subnet4
            }
        }

        :param hash: hash of the Kea DHCP config file as returned by a
        `config-hash-get` query on the kea-ctrl-agent REST server.
        """
        if len(config_json) > 1:
            raise KeaError("Did not expect len(configjson) > 1")

        dhcp_version, config_json = config_json.popitem()
        if dhcp_version == "Dhcp4":
            dhcp_version = 4
        elif dhcp_version == "Dhcp6":
            dhcp_version = 6
        else:
            raise KeaError(f"Unsupported DHCP IP version '{dhcp_version}'")

        subnets = []
        for obj in config_json.get(f"subnet{dhcp_version}", []):
            subnet = KeaDhcpSubnet.from_json(obj)
            subnets.append(subnet)
        for obj in config_json.get("shared-networks", []):
            for subobj in obj.get(f"subnet{dhcp_version}", []):
                subnet = KeaDhcpSubnet.from_json(subobj)
                subnets.append(subnet)

        return cls(
            config_hash=config_hash,
            dhcp_version=dhcp_version,
            subnets=subnets,
        )


def send_query(
    query: KeaQuery,
    address: str,
    port: int = 443,
    https: bool = True,
    session: requests.Session = None,
    timeout: int = 10,
) -> list[KeaResponse]:
    """
    Send `query` to a Kea Control Agent listening to `port` on IP
    address `address`, using either http or https

    :param https: If True, use https. Otherwise, use http.

    :param session: Optional requests.Session to be used when sending
    the query. Assumed to not be closed. session is not closed after
    the end of this call, so that session can be used for persistent
    http connections among different send_query calls.
    """
    scheme = "https" if https else "http"
    location = f"{scheme}://{address}:{port}/"
    logger.debug("send_query: sending request to %s with query %r", location, query)
    try:
        if session is None:
            r = requests.post(
                location,
                data=json.dumps(asdict(query)),
                headers={"Content-Type": "application/json"},
                timeout=timeout,
            )
        else:
            r = session.post(
                location,
                data=json.dumps(asdict(query)),
                headers={"Content-Type": "application/json"},
                timeout=timeout,
            )
    except HTTPError as err:
        logger.debug(
            "send_query: request to %s yielded an error: %d %s",
            err.request.url,
            err.response.status_code,
            err.response.reason,
            exc_info=err,
        )
        raise err
    except Timeout as err:
        logger.debug(
            "send_query: request to %s timed out", err.request.url, exc_info=err
        )
        raise err

    try:
        response_json = r.json()
    except JSONDecodeError as err:
        logger.debug(
            "send_query: expected json from %s, got %s", address, r.text, exc_info=err
        )
        raise err

    if isinstance(response_json, dict):
        err = KeaError(f"bad response from {address}: {response_json!r}")
        logger.debug(
            "send_query: expected a json list of objects from %s, got %r",
            address,
            response_json,
            exc_info=err,
        )
        raise err

    responses = []
    for obj in response_json:
        response = KeaResponse(
            obj.get("result", KeaStatus.ERROR),
            obj.get("text", ""),
            obj.get("arguments", {}),
            obj.get("service", ""),
        )
        responses.append(response)
    return responses


def unwrap(responses: list[KeaQuery], require_success=True) -> KeaQuery:
    """
    Helper function implementing the sequence of operations often done
    on the list of responses returned by `send_query()`
    """
    if len(responses) != 1:
        raise KeaError("Received invalid amount of responses")

    response = responses[0]
    if require_success and not response.success:
        raise KeaError("Did not receive a successful response")
    return response


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


@dataclass
class KeaResponse:
    """
    Class representing the response to a REST query sent to a Kea
    Control Agent.
    """

    result: int
    text: str
    arguments: dict
    service: str

    @property
    def success(self) -> bool:
        return self.result == KeaStatus.SUCCESS


@dataclass
class KeaQuery:
    """Class representing a REST query to be sent to a Kea Control Agent."""

    command: str
    arguments: dict

    # The server(s) at which the command is targeted. Usually ["dhcp4", "dhcp6"] or ["dhcp4"] or ["dhcp6"].
    service: list[str]
