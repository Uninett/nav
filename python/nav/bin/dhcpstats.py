#!/usr/bin/env python
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
Collects statistics from DHCP servers and sends them to the Graphite/Carbon
backend.
"""

import argparse
import logging
from functools import partial
import sys

from nav.config import getconfig
from nav.dhcpstats import kea_dhcp
from nav.dhcpstats.errors import CommunicationError
from nav.errors import ConfigurationError
from nav.logs import init_generic_logging
from nav.metrics import carbon
import nav.daemon

_logger = logging.getLogger("nav.dhcpstats")
LOGFILE = "dhcpstats.log"
CONFIGFILE = "dhcpstats.conf"
PIDFILE = "dhcpstats.pid"

CLIENTS = {
    "kea-dhcp4": partial(kea_dhcp.Client, dhcp_version=4),
}


def main():
    """Start collecting statistics."""
    parse_args()
    init_generic_logging(
        logfile=LOGFILE,
        stderr=True,
        stderr_level=logging.ERROR,
        read_config=True,
    )
    exit_if_already_running()
    try:
        config = getconfig(CONFIGFILE)
    except OSError as error:
        _logger.warning(error)
        config = {}
    collect_stats(config)


def parse_args():
    """
    Builds an ArgumentParser and returns parsed program arguments.
    (For now, this is called solely to support the --help option.)
    """
    parser = argparse.ArgumentParser(
        description="Collects statistics from DHCP servers and sends them to the "
        "Graphite/Carbon backend",
        epilog="Statistics are collected from each DHCP server configured in "
        "'CONFDIR/dhcpstats.conf', and then sent to the Graphite/Carbon backend "
        "configured in 'CONFDIR/graphite.conf'.",
    )
    return parser.parse_args()


def collect_stats(config):
    """
    Collects current stats from each configured server.

    :param config: dhcpstats.conf INI-parsed into a dict specifying
    servers to collect metrics from.
    """

    _logger.info("--> Starting stats collection <--")

    all_stats = []

    for client in get_clients(config):
        _logger.info(
            "Collecting stats using %s...",
            client,
        )

        try:
            fetched_stats = client.fetch_stats()
        except ConfigurationError as err:
            _logger.warning(
                "%s is badly configured: %s, skipping server...",
                client,
                err,
            )
        except CommunicationError as err:
            _logger.warning(
                "Error while collecting stats using %s: %s, skipping server...",
                client,
                err,
            )
        else:
            all_stats.extend(fetched_stats)
            _logger.info(
                "Successfully collected stats using %s",
                client,
            )

    carbon.send_metrics(all_stats)

    _logger.info("--> Stats collection done <--")


def get_clients(config):
    """
    Yields one client per correctly configured server in config. A section
    of the config correctly configures a server if:

    * Its name starts with 'endpoint_' or 'server_'.
    * It has the mandatory option 'type'.
    * The value of the 'type' option is mapped to a client initializer
      by the global CLIENTS dictionary, and the client doesn't raise a
      ConfigurationError when it is initialized with the rest of the
      options of the section as keyword arguments.

    :param config: dhcpstats.conf INI-parsed into a dict specifying
    servers to collect metrics from.
    """
    for section, options in config.items():
        if section.startswith("endpoint_"):
            server_name = section.removeprefix("endpoint_")
        elif section.startswith("server_"):
            server_name = section.removeprefix("server_")
        else:
            continue
        server_type = options.get("type")
        kwargs = {opt: val for opt, val in options.items() if opt != "type"}
        try:
            cls = CLIENTS[server_type]
        except KeyError:
            _logger.warning(
                "Invalid server type '%s' defined in config section [%s], skipping "
                "server...",
                server_type,
                section,
            )
            continue

        try:
            client = cls(server_name, **kwargs)
        except (ConfigurationError, TypeError) as err:
            _logger.warning(
                "Section [%s] of %s is badly configured: %s, skipping server...",
                section,
                CONFIGFILE,
                err,
            )
        else:
            yield client


def exit_if_already_running():
    try:
        nav.daemon.justme(PIDFILE)
        nav.daemon.writepidfile(PIDFILE)
    except nav.daemon.AlreadyRunningError:
        _logger.error(
            "Attempted to start a new dhcp stats collection process while another is "
            "running. This is likely due to stats collection taking longer than the "
            "cron interval"
        )
        sys.exit(1)
    except nav.daemon.DaemonError as error:
        _logger.error("%s", error)
        sys.exit(1)


if __name__ == "__main__":
    main()
