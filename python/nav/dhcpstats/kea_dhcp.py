#
# Copyright (C) 2025 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Fetch DHCP stats from Kea DHCP servers, using the Kea API
"""

from dataclasses import dataclass
from enum import IntEnum
from functools import partial
from itertools import chain
import json
import logging
import time
from typing import Callable, Optional, Iterator

from IPy import IP
from requests import RequestException, JSONDecodeError, Session
from requests.adapters import HTTPAdapter, Retry

from nav.dhcpstats.common import DhcpPath, GraphiteMetric
from nav.dhcpstats.errors import (
    CommunicationError,
    KeaEmpty,
    KeaError,
    KeaConflict,
    KeaUnexpected,
    KeaUnsupported,
)
from nav.errors import ConfigurationError

_logger = logging.getLogger(__name__)


@dataclass(order=True, frozen=True)
class Pool:
    """
    A pool configured in a Kea DHCP server.

    Note that what is called a pool in Kea is more specifically called a range
    in NAV because it is guaranteed to contain all IP addresses between a first
    and a last IP address (inclusive) whereas a pool in NAV might contain gaps.
    """

    subnet_id: int
    pool_id: int

    group_name: Optional[str]
    first_ip: IP
    last_ip: IP

    def __str__(self):
        if self.group_name is None:
            group_subsentence = ""
        else:
            group_subsentence = f" and in group '{self.group_name}'"
        return (
            f"Kea pool {self.pool_id} from {self.first_ip} to {self.last_ip} "
            f"in Kea subnet {self.subnet_id}{group_subsentence}"
        )


class Client:
    """
    Fetches DHCP stats for each pool configured in a Kea DHCP server by using
    its Kea API. See 'Client.fetch_stats()'.

    Note: This client does not assume that any hooks have been installed into
          the Kea DHCP server. Kea offers a 'lease-stats' hook that comes with
          extra API commands which become necessary to use if one want reliable
          stats when using a setup where multiple Kea DHCP servers share the
          same underlying lease database since the standard API commands issue a
          server's cache, not the underlying database. This client does not use
          the hook. Anyhow, the hook doesn't support fetching statistics on a
          per-pool basis, only per-subnet basis, which is too coarse for us.
          See https://kea.readthedocs.io/en/kea-2.6.3/arm/hooks.html#libdhcp-stat-cmds-so-statistics-commands-for-supplemental-lease-statistics.
    """

    def __init__(
        self,
        server_name: str,
        url: str,
        dhcp_version: int = 4,
        http_basic_username: str = "",
        http_basic_password: str = "",
        client_cert_path: str = "",
        client_cert_key_path: str = "",
        user_context_groupname_key: str = "group",
        timeout: float = 5.0,
    ):
        self._server_name: str = server_name
        self._url: str = url
        self._dhcp_version: int = dhcp_version
        self._http_basic_username: str = http_basic_username
        self._http_basic_password: str = http_basic_password
        self._client_cert_path: str = client_cert_path
        self._client_key_path: str = client_cert_key_path
        self._user_context_groupname_key: str = user_context_groupname_key
        self._timeout: float = timeout

        self._kea_config: Optional[dict] = None
        self._session: Optional[Session] = None
        self._start_time: float = time.time()

        if dhcp_version == 4:
            # self._api_extractors is a map from the name of stats in NAV to
            # functions that extract that stat from a dict previously returned
            # by the Kea API containing all stats
            self._api_extractors: tuple[
                tuple[str, Callable[[dict, Pool], int]], ...
            ] = (
                ("total", partial(_extract_pool_stat, name="total-addresses")),
                ("assigned", partial(_extract_pool_stat, name="assigned-addresses")),
                ("declined", partial(_extract_pool_stat, name="declined-addresses")),
                (
                    "unassigned",
                    lambda stats, pool: (
                        _extract_pool_stat(stats, pool, name="total-addresses")
                        - _extract_pool_stat(stats, pool, name="assigned-addresses")
                    ),
                ),
            )
        else:
            raise ConfigurationError(f"DHCPv{dhcp_version} is not supported")

    def __str__(self):
        return (
            f"API client for Kea DHCPv{self._dhcp_version} server "
            f"'{self._server_name}' at {self._url}"
        )

    def fetch_stats(self) -> list[GraphiteMetric]:
        """
        Fetches and returns a list containing the most recent stats of interest
        for each pool configured in the Kea DHCP server. The stats of interest
        are:

        * The total amount of addresses in that Kea pool.
          (Named "total" addresses in NAV.)

        * The amount of currently assigned (aka. leased) addresses in that Kea pool.
          (Named "assigned" addresses in NAV.)

        * The amount of declined addresses in that Kea pool. That is, addresses in
          that Kea pool that are erroneously used by unknown entities and therefore
          not available for assignment. The set of declined addresses is a
          subset of the set of assigned addresses.
          (Named "declined" addresses in NAV.)

        * The amount of currently unassigned addresses in that Kea pool.
          (Named "unassigned" addresses in NAV.)

        If the Kea API responds with an empty response to one or more of the
        stats of interest for a Kea pool, these stats will be missing in the
        returned list, but a list is still succesfully returned. Other errors
        during this call will cause a subclass of
        nav.dhcpstats.errors.CommunicationError or nav.errors.ConfigurationError
        to be raised.
        """

        self._session = self._create_session()
        self._start_time = time.time()

        kea_config = self._fetch_kea_config()
        raw_stats = self._fetch_raw_stats()

        subnets = self._subnets_of_kea_config(kea_config)
        pools = list(
            chain.from_iterable(self._pools_of_subnet(subnet) for subnet in subnets)
        )
        stats = list(
            chain.from_iterable(self._stats_of_pool(raw_stats, pool) for pool in pools)
        )

        self._log_consistency_with_upstream_pools(pools)
        self._log_runtime(
            start_time=self._start_time,
            end_time=time.time(),
            n_stats=len(stats),
            n_pools=len(pools),
        )

        self._session.close()
        self._session = None
        return stats

    def _fetch_raw_stats(self) -> dict:
        """
        Returns all statistics recorded by the Kea DHCP server.
        (API command: 'statistic-get-all')
        """
        response = self._send_query("statistic-get-all")
        return response.get("arguments", {})

    def _fetch_kea_config(self) -> dict:
        """
        Returns the current configuration of the Kea DHCP server.
        (API command: 'config-get'.)
        """
        if (
            self._kea_config is None
            or (kea_config_hash := self._kea_config.get("hash", None)) is None
            or kea_config_hash != self._fetch_kea_config_hash()
        ):
            response = self._send_query("config-get")
            self._kea_config = response.get("arguments", {}).get(
                f"Dhcp{self._dhcp_version}", None
            )
            if not isinstance(self._kea_config, dict):
                raise KeaUnexpected("Unrecognizable response to a 'config-get' request")
        return self._kea_config

    def _fetch_kea_config_hash(self) -> Optional[str]:
        """
        Returns the hash of the current configuration of the Kea DHCP server.
        (API command: 'config-hash-get'.)
        """
        try:
            return (
                self._send_query("config-hash-get")
                .get("arguments", {})
                .get("hash", None)
            )
        except CommunicationError as err:
            _logger.debug(str(err))
            return None

    def _send_query(self, command: str, **kwargs) -> dict:
        """
        Returns the response from the Kea API to the given command instructed
        towards the underlying Kea DHCP server. Keyword arguments to this
        function will be passed along as arguments to the command.

        Communication errors (HTTP errors, JSON errors, access control errors,
        unrecognized json response formats) cause a CommunicationError to be
        raised. If possible, it is reraised from a more descriptive error such
        as an HTTPError.

        Valid Kea API responses that indicate a failure on the server-end cause
        a descriptive Kea-specific subclass of CommunicationError to be raised.

        A ConfigurationError is raised if this client is configured in such a
        way that it can't be consistent with its own configuration while still
        properly communicating with the Kea API (for example when the use of
        client certificates, which require TLS, is enabled but HTTPS is
        disabled).
        """
        session = self._session or self._create_session()

        _logger.debug("Sending command '%s' to Kea API at %s", command, self._url)

        post_data = json.dumps(
            {
                "command": command,
                "arguments": kwargs,
                "service": [f"dhcp{self._dhcp_version}"],
            }
        )

        try:
            responses = session.post(
                self._url,
                data=post_data,
                timeout=self._timeout,
                headers={"Content-Type": "application/json"},
            )
            _logger.debug(
                "HTTP response status to command '%s' from %s was 'HTTP %s: %s'",
                command,
                self._url,
                responses.status_code,
                responses.reason,
            )
            responses.raise_for_status()
            responses = responses.json()
        except JSONDecodeError as err:
            raise KeaUnexpected(
                f"{self._url} does not look like a Kea API; "
                f"response to command {command} was not valid JSON",
            ) from err
        except RequestException as err:
            raise CommunicationError from err

        # Any valid response from Kea is a JSON list with one entry corresponding to the
        # response from the dhcp server "service" we queried
        if not (
            isinstance(responses, list)
            and len(responses) == 1
            and isinstance((response := responses[0]), dict)
            and "result" in response
            and isinstance((status := response["result"]), int)
        ):
            if (
                isinstance(responses, dict)
                and "result" in responses
                and "text" in responses
                and isinstance((status := responses["result"]), int)
                and isinstance((message := responses["text"]), str)
            ):
                # If the response is a JSON object it's a specific error message
                # See https://kea.readthedocs.io/en/kea-2.6.0/arm/ctrl-channel.html#control-agent-command-response-format
                raise KeaUnexpected(f"{status}: {message}")
            else:
                # Otherwise, something odd is happening
                raise KeaUnexpected(
                    f"{self._url} does not look like a Kea API; "
                    "response JSON structured in an unknown way",
                )

        _logger.debug(
            "API response status to command '%s' from %s was 'Kea %s: %s'",
            command,
            self._url,
            status,
            response.get("text", _KeaStatus.describe(status)),
        )

        _raise_for_kea_status(status)

        return response

    def _create_session(self) -> Session:
        """
        Creates and returns an HTTP session with authentication based on
        credentials passed during object initialization.
        """
        _logger.debug(
            "Creating new HTTP/HTTPS session for use with Kea API at %s", self._url
        )

        session = Session()

        retries = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods={"POST"},
        )

        session.mount("https://", HTTPAdapter(max_retries=retries))
        session.mount("http://", HTTPAdapter(max_retries=retries))

        https = self._url.lower().startswith("https://")

        if https:
            _logger.debug("Using HTTPS")
        else:
            _logger.warning(
                "Using HTTP to request potentially sensitive data such as API passwords"
            )

        if self._http_basic_username and self._http_basic_password:
            _logger.debug("Using HTTP Basic Authentication")
            if not https:
                _logger.warning("Using HTTP Basic Authentication without HTTPS")
            session.auth = (self._http_basic_username, self._http_basic_password)
        else:
            _logger.debug("Not using HTTP Basic Authentication")

        if self._client_cert_path:
            _logger.debug("Using client certificate authentication")
            if not https:
                raise ConfigurationError(
                    "Authentication using client certificates is only available for "
                    "urls with HTTPS scheme"
                )
            _logger.debug("Certificate path: '%s'", self._client_cert_path)
            if self._client_key_path:
                _logger.debug("Certificate key path: '%s'", self._client_key_path)
                session.cert = (self._client_cert_path, self._client_key_path)
            else:
                session.cert = self._client_cert_path
        else:
            _logger.debug("Not using client certificate authentication")

        return session

    def _subnets_of_kea_config(self, config: dict) -> Iterator[dict]:
        """
        Returns one subnet-dict per subnet configured under "subnet" or under
        "shared-networks" of a Kea DHCP configuration.
        """
        subnetkey = f"subnet{self._dhcp_version}"

        standalone_subnets = config.get(subnetkey, [])
        shared_network_subnets = chain.from_iterable(
            shared_network_config.get(subnetkey, [])
            for shared_network_config in config.get("shared-networks", [])
        )

        yield from chain(standalone_subnets, shared_network_subnets)

    def _pools_of_subnet(self, subnet: dict) -> Iterator[Pool]:
        """
        Returns one Pool instance per pool configured under "pools" of a subnet
        of a Kea DHCP configuration.
        """
        try:
            subnet_id = int(subnet["id"])
        except (KeyError, TypeError, ValueError):
            _logger.error(
                "Misconfigured subnet from %s, skipping subnet...",
                self._url,
            )
            return

        used_pool_ids = set()
        for pool in subnet.get("pools", []):
            try:
                pool_id = int(pool["pool-id"])
                first_ip, last_ip = self._bounds_of_pool_range(pool["pool"])
                group_name = self._group_name_of_pool(pool)
            except (AttributeError, KeyError, TypeError, ValueError):
                _logger.error(
                    'Could not parse Kea pool in subnet %d from %s, skipping Kea '
                    'pool... (make sure every Kea pool has "pool-id" and "pool" '
                    'configured in the Kea DHCP configuration)',
                    subnet_id,
                    self._url,
                )
                continue

            if pool_id not in used_pool_ids:
                yield Pool(
                    subnet_id=subnet_id,
                    pool_id=pool_id,
                    group_name=group_name,
                    first_ip=first_ip,
                    last_ip=last_ip,
                )
                used_pool_ids.add(pool_id)
            else:
                _logger.warning(
                    "Subnet %d from %s has multiple pools with the pool_id %d; "
                    "due to this, the pool from %s to %s with pool_id %d will be "
                    "ignored by NAV",
                    subnet_id,
                    self._url,
                    pool_id,
                    first_ip,
                    last_ip,
                    pool_id,
                )

    def _stats_of_pool(self, raw_stats: dict, pool: Pool) -> Iterator[GraphiteMetric]:
        """
        Returns as graphite metric tuples the most recent stats of interest in
        raw_stats, for the given Kea pool.

        raw_stats is a dictionary representing the result of the Kea API command
        'statistic-get-all'.
        """
        try:
            path_prefix = DhcpPath.from_external_info(
                server_name=self._server_name,
                allocation_type="range",
                group_name=pool.group_name,
                first_ip=pool.first_ip,
                last_ip=pool.last_ip,
            )
        except ValueError as err:
            _logger.error(
                "Error when creating graphite path for %s: %s",
                pool,
                err,
            )
            return

        for nav_stat_name, extractor in self._api_extractors:
            try:
                value = extractor(raw_stats, pool)
            except ValueError as err:
                _logger.warning(
                    "%s could not infer any value for the stat named '%s' for %s (%s). "
                    "Skipping this stat for this pool (which will cause gaps in any "
                    "related graph for this pool)",
                    self,
                    nav_stat_name,
                    pool,
                    err,
                )
            else:
                path = path_prefix.to_graphite_path(nav_stat_name)
                yield (path, (self._start_time, value))

    def _bounds_of_pool_range(self, pool_range: str) -> tuple[IP, IP]:
        """
        Returns a pair where the first element is the first IP and the second
        element is the last IP of a string used in the Kea DHCP configuration
        file for representing a range of IP addresses. Example:

        > self._bounds_of_pool_range("10.0.0.0 - 10.0.0.10")
        > IP(10.0.0.0), IP(10.0.0.10)

        > self._bounds_of_pool_range("10.0.0.0/24")
        > IP(10.0.0.0), IP(10.0.0.255)
        """
        if "-" in pool_range:
            # x.x.x.x - x.x.x.x
            range_start, _, range_end = pool_range.partition("-")
            range_start = IP(range_start.strip())
            range_end = IP(range_end.strip())
        else:
            # x.x.x.x/m
            ip = IP(pool_range.strip())
            range_start = ip[0]
            range_end = ip[-1]
        return range_start, range_end

    def _group_name_of_pool(self, pool: dict) -> Optional[str]:
        """
        Looks for a group name in a pool of a Kea DHCP configuration. Returns
        group name if found, else returns None.
        """
        group_name_key = self._user_context_groupname_key
        group_name = pool.get("user-context", {}).get(group_name_key, None)
        if not isinstance(group_name, str):
            _logger.debug(
                '%s did not find a group name when looking up "%s" in "user-context" '
                'for a Kea pool',
                self,
                group_name_key,
            )
            return None
        return group_name

    def _log_consistency_with_upstream_pools(self, local_pools: list):
        """
        The part of the Kea API that deal with pools identify each Kea pool by
        ID. This function logs a warning if the mapping between pool ID and pool
        object differs between the pools known to the client (local_pools) and
        the pools known to the Kea API right now.
        """
        upstream_config = self._fetch_kea_config()
        upstream_subnets = self._subnets_of_kea_config(upstream_config)
        upstream_pools = list(
            chain.from_iterable(
                self._pools_of_subnet(subnet) for subnet in upstream_subnets
            )
        )

        if sorted(local_pools) != sorted(upstream_pools):
            _logger.warning(
                "The Kea DHCPv4 server's pool configuration was modified while stats "
                "were being fetched. This may cause stats collected during this run to "
                "be associated with the wrong Kea pool (and subsequently wrong range "
                "in NAV)."
            )

    def _log_runtime(
        self, start_time: float, end_time: float, n_stats: int, n_pools: int
    ):
        """
        Logs a debug message about the time spent during a 'self.fetch_stats()'
        run and the amount of Kea pools and stats seen.
        """
        _logger.debug(
            "Fetched %d stats from %d Kea pool(s) in %.2f seconds from %s",
            n_stats,
            n_pools,
            end_time - start_time,
            self._url,
        )


def _extract_pool_stat(raw_stats: dict, pool: Pool, name: str) -> int:
    """
    Returns the value of the most recent stat in raw_stats with the given name
    for the given pool.

    raw_stats is a dictionary representing the result of the Kea API command
    'statistic-get-all'.
    """
    statistic = f"subnet[{pool.subnet_id}].pool[{pool.pool_id}].{name}"
    samples = raw_stats.get(statistic, [])
    if len(samples) == 0:
        raise ValueError(
            f"No values found when looking up '{statistic}' in API response"
        )
    # The reference API client assumes samples[0] is the most recent sample
    # See https://gitlab.isc.org/isc-projects/stork/-/blob/4193375c01e3ec0b3d862166e2329d76e686d16d/backend/server/apps/kea/rps.go#L223-227
    value, _timestring = samples[0]
    return value


class _KeaStatus(IntEnum):
    """Status of a response sent from a Kea API"""

    SUCCESS = 0
    ERROR = 1
    UNSUPPORTED = 2
    EMPTY = 3
    CONFLICT = 4

    @classmethod
    def describe(cls, status: int) -> str:
        try:
            return cls(status).name
        except ValueError:
            return "(status has no description)"


def _raise_for_kea_status(status: int):
    """
    Raises a suitable Kea-specific subclass of CommunicationError if status is
    not _KeaStatus.SUCCESS.
    """
    if status == _KeaStatus.SUCCESS:
        return
    elif status == _KeaStatus.UNSUPPORTED:
        raise KeaUnsupported
    elif status == _KeaStatus.EMPTY:
        raise KeaEmpty
    elif status == _KeaStatus.ERROR:
        raise KeaError
    elif status == _KeaStatus.CONFLICT:
        raise KeaConflict
    else:
        raise KeaUnexpected("Unknown response status")
