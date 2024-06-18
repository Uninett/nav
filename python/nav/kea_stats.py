"""
Functions for querying the Kea Control Agent for statistics from Kea DHCP
servers.

Stork (https://gitlab.isc.org/isc-projects/stork) is used as a guiding
implementation for interacting with the Kea Control Agent.  See also the Kea
Control Agent documentation
(https://kea.readthedocs.io/en/kea-2.6.0/arm/agent.html).
"""
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import requests
from requests.exceptions import JSONDecodeError, HTTPError
from typing import Union

logger = logging.getLogger(__name__)

class KeaStatus(Enum):
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
    Class for defining a REST response on a REST query sent to a kea-ctrl-agent
    process.
    """
    result: int
    text: str
    arguments: dict[str: Union[str, int]]
    service: str

@dataclass
class KeaQuery:
    """
    Class for defining a REST query to be sent to a kea-ctrl-agent
    process.
    """
    command: str
    arguments: dict[str: Union[str, int]]
    services: list[str] # The server(s) at which the command is targeted. Usually ["dhcp4", "dhcp6"] or ["dhcp4"] or ["dhcp6"].

    def send(self, address) -> list[KeaResponse]:
        """
        Send this query to a kea-ctrl-agent located at address
        """
        logger.debug("KeaQuery.send: sending request to %s with query %r", address, self)
        try:
            r = requests.post(address, data=asdict(self))
        except HTTPError as err:
            logger.error("KeaQuery.send: request to %s yielded an error: %d %s", err.url, err.status_code, err.reason)
            raise err

        try:
            json = r.json()
        except JSONDecodeError as err:
            logger.error("KeaQuery.send: expected json from %s, got %s", address, r.text)
            raise err

        responses = []
        for obj in json:
            response = KeaResponse(
                obj.get("result", KeaStatus.ERROR),
                obj.get("text", ""),
                obj.get("arguments", {}),
                obj.get("service", ""),
            )
            responses.append(response)
        return responses
