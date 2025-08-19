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
from itertools import chain
import json
import logging
import time
from typing import Optional, Iterator

from IPy import IP
from requests import RequestException, JSONDecodeError, Session
from requests.adapters import HTTPAdapter, Retry

from nav.dhcpstats.errors import (
    CommunicationError,
    KeaEmpty,
    KeaError,
    KeaConflict,
    KeaUnexpected,
    KeaUnsupported,
)
from nav.errors import ConfigurationError
from nav.metrics.templates import metric_path_for_dhcp_pool


_logger = logging.getLogger(__name__)


@dataclass(order=True, frozen=True)
class Pool:
    """A Kea DHCP configured address pool"""

    subnet_id: int
    pool_id: int

    name: str
    range_start: IP
    range_end: IP


GraphiteMetric = tuple[str, tuple[float, int]]


class Client:
    """
    Fetches DHCP stats for each address pool managed by some Kea DHCP server by using
    the Kea API. See 'Client.fetch_stats()'.

    Note: This client assumes no hooks have been installed into the Kea DHCP
          server. The 'lease-stats' hook is required for reliable stats when
          multiple servers share the same lease database because the standard
          commands issue the cache, not the DB. This client does not support the
          hook. Anyhow, the hook doesn't support fetching statistics on a
          per-pool basis, only per-subnet basis, which is too coarse for us.
          See https://kea.readthedocs.io/en/kea-2.6.3/arm/hooks.html#libdhcp-stat-cmds-so-statistics-commands-for-supplemental-lease-statistics.
    """

    def __init__(
        self,
        name: str,
        url: str,
        dhcp_version: int = 4,
        http_basic_username: str = "",
        http_basic_password: str = "",
        client_cert_path: str = "",
        client_cert_key_path: str = "",
        user_context_poolname_key: str = "name",
        timeout: float = 5.0,
    ):
        self._name: str = name
        self._url: str = url
        self._dhcp_version: int = dhcp_version
        self._http_basic_user: str = http_basic_username
        self._http_basic_password: str = http_basic_password
        self._client_cert_path: str = client_cert_path
        self._client_key_path: str = client_cert_key_path
        self._user_context_poolname_key: str = user_context_poolname_key
        self._timeout: float = timeout

        self._kea_config: Optional[dict] = None
        self._session: Optional[Session] = None
        self._start_time: float = time.time()

        if dhcp_version == 4:
            # self._api_namings is a map between how stats are named in NAV and how
            # stats are named in Kea.
            self._api_namings = (
                ("total", "total-addresses"),
                ("assigned", "assigned-addresses"),
                ("declined", "declined-addresses"),
            )
        else:
            raise ConfigurationError(f"DHCPv{dhcp_version} is not supported")

    def __str__(self):
        return (
            f"API client for Kea DHCPv{self._dhcp_version} endpoint '{self._name}' at "
            f"{self._url}"
        )

    def fetch_stats(self) -> list[GraphiteMetric]:
        """
        Fetches and returns a list containing the most recent stats of interest
        for each DHCP address pool. The stats of interest are:

        * The total amount of addresses in that pool.
          (Named "total" addresses in NAV.)

        * The amount of currently assigned (aka. leased) addresses in that pool.
          (Named "assigned" addresses in NAV.)

        * The amount of declined addresses in that pool. That is, addresses in
          that pool that are erroneously used by unknown entities and therefore
          not available for assignment. The set of declined addresses is a
          subset of the set of assigned addresses.
          (Named "declined" addresses in NAV.)

        If the Kea API responds with an empty response to one or more of the
        stats of interest for a pool, these stats will be missing in the
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
        Returns the hash of the current configation of the Kea DHCP server.
        (API command: 'config-hash-get'.)
        """
        try:
            return (
                self._send_query("config-hash-get")
                .get("arguments", {})
                .get("hash", None)
            )
        except KeaUnsupported as err:
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
                f"{self._url} does not look like a Kea API endpoint; "
                f"response to command {command} was not valid JSON",
            ) from err
        except RequestException as err:
            raise CommunicationError from err

        # Any valid response from Kea is a JSON list with one entry corresponding to the
        # response from either the dhcp4 or dhcp6 service we queried
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

        https = self._url.startswith("https://")

        if https:
            _logger.debug("Using HTTPS")
        else:
            _logger.warning(
                "Using HTTP to request potentially sensitive data such as API passwords"
            )

        if self._http_basic_user and self._http_basic_password:
            _logger.debug("Using HTTP Basic Authentication")
            if not https:
                _logger.warning("Using HTTP Basic Authentication without HTTPS")
            session.auth = (self._http_basic_user, self._http_basic_password)
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

        for pool in subnet.get("pools", []):
            try:
                pool_id = int(pool["pool-id"])
                pool_start, pool_end = self._bounds_of_pool_range(pool["pool"])
                pool_name = self._name_of_pool(
                    pool,
                    fallback=f"pool-{pool_start.strNormal()}-{pool_end.strNormal()}",
                )
            except (AttributeError, KeyError, TypeError, ValueError):
                _logger.error(
                    'Could not parse pool in subnet %d from %s, skipping pool... '
                    '(make sure every pool has "pool-id" and "pool" configured in the '
                    'Kea DHCP configuration)',
                    subnet_id,
                    self._url,
                )
                continue

            yield Pool(
                subnet_id=subnet_id,
                pool_id=pool_id,
                name=pool_name,
                range_start=pool_start,
                range_end=pool_end,
            )

    def _stats_of_pool(self, raw_stats: dict, pool: Pool) -> Iterator[GraphiteMetric]:
        """
        Returns as graphite metric tuples the most recent stats of interest in
        raw_stats, for the given pool.

        raw_stats is a dictionary representing the result of the Kea API command
        'statistic-get-all'.
        """

        for nav_stat_name, api_stat_name in self._api_namings:
            statistic = f"subnet[{pool.subnet_id}].pool[{pool.pool_id}].{api_stat_name}"
            samples = raw_stats.get(statistic, [])
            if len(samples) == 0:
                _logger.info(
                    "No stats found when querying for '%s' in pool having range "
                    "'%s-%s' and name '%s'",
                    api_stat_name,
                    pool.range_start,
                    pool.range_end,
                    pool.name,
                )
            else:
                # The reference API client assumes samples[0] is the most recent sample
                # See https://gitlab.isc.org/isc-projects/stork/-/blob/4193375c01e3ec0b3d862166e2329d76e686d16d/backend/server/apps/kea/rps.go#L223-227
                value, _timestring = samples[0]
                path = metric_path_for_dhcp_pool(
                    self._dhcp_version,
                    self._name,
                    pool.name,
                    pool.range_start,
                    pool.range_end,
                    nav_stat_name,
                )
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

    def _name_of_pool(self, pool: dict, fallback: str) -> str:
        """
        Looks for a pool name in a pool of a Kea DHCP configuration.
        Returns pool name if found, else returns a fallback name.
        """
        pool_name_key = self._user_context_poolname_key
        pool_name = pool.get("user-context", {}).get(pool_name_key, None)
        if not isinstance(pool_name, str):
            _logger.debug(
                '%s did not find a pool name when looking up "%s" in "user-context" '
                'for a pool, defaulting to name "%s"... ',
                self,
                pool_name_key,
                fallback,
            )
            return fallback
        return pool_name

    def _log_consistency_with_upstream_pools(self, local_pools: list):
        """
        The part of the Kea API that deal with pools identify each pool by
        ID. This function logs a warning if the mapping between pool ID and pool
        object differs between the pools stored in the client (local_pools) and
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
                "The DHCP server's address pool configuration was modified while stats "
                "were being fetched. This may cause stats collected during this run to "
                "be associated with the wrong address pool."
            )

    def _log_runtime(
        self, start_time: float, end_time: float, n_stats: int, n_pools: int
    ):
        """
        Logs a debug message about the time spent during a 'self.fetch_stats()'
        run and the amount of pools and stats seen.
        """
        _logger.debug(
            "Fetched %d stats from %d pool(s) in %.2f seconds from %s",
            n_stats,
            n_pools,
            end_time - start_time,
            self._url,
        )


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
