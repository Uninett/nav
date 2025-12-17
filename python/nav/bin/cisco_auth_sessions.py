#!/usr/bin/env python
# -*- testargs: -h -*-
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
# details. You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
A command line program to query Cisco authentication sessions.

This research tool queries CISCO-AUTH-FRAMEWORK-MIB to investigate 802.1X
and MAC Authentication Bypass (MAB) sessions on Cisco switches, displaying
VLAN assignments per interface.

Related to Issue #3607.
"""

import sys
import argparse
import logging
from collections import defaultdict

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from nav.util import is_valid_ip
from nav.ipdevpoll.snmp.common import SnmpError, SNMPParameters
from nav.ipdevpoll.snmp import AgentProxy, snmpprotocol
from nav.models.manage import Netbox
from nav.mibs.cisco_auth_framework_mib import CiscoAuthFrameworkMib
from nav.mibs.if_mib import IfMib
from nav.logs import init_generic_logging

from twisted.internet import reactor, defer

TIMEOUT = SNMPParameters.DEFAULT_TIMEOUT
_exit_code = 0
_logger = logging.getLogger('cisco_auth_sessions')


def main():
    options = parse_args()

    # Set up logging - simple formatter for CLI output
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    init_generic_logging(
        stderr=True,
        formatter=formatter,
        rootlogger='cisco_auth_sessions',
    )

    # Set log level based on verbose flag
    if options.verbose:
        _logger.setLevel(logging.DEBUG)
    else:
        _logger.setLevel(logging.ERROR)

    reactor.callWhenRunning(reactor_main, options.device, options.port, options.timeout)
    reactor.run()
    sys.exit(_exit_code)


def reactor_main(netbox, port, timeout):
    """The main function to start in the event reactor"""
    print_header(netbox, port)
    df = defer.ensureDeferred(query_and_display(netbox, port, timeout))
    df.addErrback(failure_handler)
    df.addBoth(endit)
    return df


async def query_and_display(netbox, port, timeout):
    """Query SNMP and display authentication session results"""
    agent = _create_agentproxy(netbox, port, timeout)
    if not agent:
        _logger.error("Could not create SNMP agent")
        return

    # Create MIB retriever instances
    caf_mib = CiscoAuthFrameworkMib(agent)
    if_mib = IfMib(agent)

    _logger.debug("Querying CISCO-AUTH-FRAMEWORK-MIB cafSessionTable...")

    # Query authentication sessions
    sessions = await caf_mib.get_auth_session_vlans()

    _logger.debug("Found %d session entries", len(sessions))
    _logger.debug("Querying IF-MIB for interface info...")

    # Query interface information
    ifnames = await if_mib.get_ifnames()  # Returns {ifindex: (ifName, ifDescr)}
    ifaliases = await if_mib.get_ifaliases()  # Returns {ifindex: ifAlias}

    # Process and display results
    display_results(sessions, ifnames, ifaliases)


def process_auth_sessions(sessions):
    """Group authentication sessions by ifIndex

    Args:
        sessions: Dict mapping table index to session data

    Returns:
        dict: {ifIndex: {'vlans': set(), 'session_count': int}}
    """
    by_port = defaultdict(lambda: {'vlans': set(), 'session_count': 0})

    for index, data in sessions.items():
        # The index is a tuple where the first element is ifIndex
        # and the rest is the sessionId (which may be multi-part)
        if isinstance(index, tuple) and len(index) >= 1:
            ifindex = index[0]
        else:
            # Fallback if index is not a tuple
            continue

        vlan = data.get('cafSessionAuthVlan')
        if vlan and vlan > 0:  # Skip VLAN 0 (no VLAN assigned)
            by_port[ifindex]['vlans'].add(vlan)
        by_port[ifindex]['session_count'] += 1

    return by_port


def display_results(sessions, ifnames, ifaliases):
    """Process and display authentication session results"""
    sessions_by_port = process_auth_sessions(sessions)

    if not sessions_by_port:
        print("\nNo active authentication sessions found on this device")
        return

    total = sum(s['session_count'] for s in sessions_by_port.values())
    _logger.debug("%d sessions across %d interfaces\n", total, len(sessions_by_port))

    # Prepare table data
    rows = []
    for ifindex in sorted(sessions_by_port.keys()):
        data = sessions_by_port[ifindex]

        # Get interface name (ifnames returns tuple of (ifName, ifDescr))
        ifname_tuple = ifnames.get(ifindex, ('N/A', ''))
        ifname = ifname_tuple[0] if isinstance(ifname_tuple, tuple) else ifname_tuple

        # Get interface alias
        ifalias = ifaliases.get(ifindex, '')

        # Format VLANs as sorted list
        vlans = sorted(data['vlans']) if data['vlans'] else []
        vlan_str = ','.join(str(v) for v in vlans) if vlans else '-'

        rows.append(
            {
                'ifindex': ifindex,
                'ifname': ifname,
                'ifalias': ifalias,
                'vlans': vlan_str,
                'sessions': data['session_count'],
            }
        )

    # Calculate maximum column widths
    col_ifindex = max(len('ifIndex'), max(len(str(r['ifindex'])) for r in rows))
    col_ifname = max(len('ifName'), max(len(r['ifname']) for r in rows))
    col_ifalias = max(len('ifAlias'), max(len(r['ifalias']) for r in rows))
    col_vlans = max(len('VLANs'), max(len(r['vlans']) for r in rows))
    col_sessions = max(len('Sessions'), max(len(str(r['sessions'])) for r in rows))

    header = (
        f"{'ifIndex':<{col_ifindex}}  "
        f"{'ifName':<{col_ifname}}  "
        f"{'ifAlias':<{col_ifalias}}  "
        f"{'VLANs':<{col_vlans}}  "
        f"{'Sessions':<{col_sessions}}"
    )
    print(header)
    print('-' * len(header))

    for row in rows:
        print(
            f"{row['ifindex']:<{col_ifindex}}  "
            f"{row['ifname']:<{col_ifname}}  "
            f"{row['ifalias']:<{col_ifalias}}  "
            f"{row['vlans']:<{col_vlans}}  "
            f"{row['sessions']:<{col_sessions}}"
        )

    total_sessions = sum(s['session_count'] for s in sessions_by_port.values())
    print(
        f"\nSummary: {len(sessions_by_port)} interfaces with active "
        f"authentication sessions, {total_sessions} total sessions"
    )


def print_header(netbox, port):
    """Print device header"""
    header = f"Device: {netbox.sysname} ({netbox.ip}:{port})"
    print(header)
    print("-" * len(header))
    print()


def failure_handler(failure):
    """Sets a non-zero exit code on failures"""
    global _exit_code
    _exit_code = 1
    return failure


def endit(result):
    """Stops the reactor"""
    from twisted.python.failure import Failure

    if isinstance(result, Failure):
        result.printTraceback(sys.stderr)
    reactor.stop()
    return result


def parse_args():
    """Parses the command line arguments"""
    parser = argparse.ArgumentParser(
        description="Queries Cisco authentication sessions (802.1X/MAB) "
        "and displays VLAN assignments per interface",
        usage="%(prog)s device",
    )
    parser.add_argument(
        'device',
        type=device,
        help="The NAV-monitored IP device to query. Must be either "
        "a sysname prefix or an IP address.",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        help="change the portnumber, [default: 161]",
        metavar="PORT",
        default=161,
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=float,
        help=f"set a non-standard timeout in seconds, [default: {TIMEOUT}]",
        default=TIMEOUT,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="enable verbose debug output",
    )
    return parser.parse_args()


def device(devicestring):
    """Converts a device specification string into a Netbox object"""
    netbox = None
    ip = is_valid_ip(devicestring)
    if ip:
        try:
            netbox = Netbox.objects.get(ip=ip)
        except Netbox.DoesNotExist:
            pass

    if not netbox:
        netbox = Netbox.objects.filter(sysname__startswith=devicestring)
        if len(netbox) > 1:
            msg = "%s matches multiple IP devices: %s" % (
                devicestring,
                ", ".join(str(box) for box in netbox),
            )
            raise argparse.ArgumentTypeError(msg)
        elif len(netbox) == 0:
            msg = "No match found for %s" % devicestring
            raise argparse.ArgumentTypeError(msg)
        else:
            netbox = netbox[0]

    if not netbox.get_preferred_snmp_management_profile():
        msg = "No SNMP management profile set for %s" % netbox
        raise argparse.ArgumentTypeError(msg)

    return netbox


def _create_agentproxy(netbox, port, timeout=TIMEOUT):
    """Create SNMP AgentProxy for the given netbox"""
    params = SNMPParameters.factory(netbox, timeout=timeout)
    if not params:
        return

    snmp_port = snmpprotocol.port()
    agent = AgentProxy(
        netbox.ip, port, protocol=snmp_port.protocol, snmp_parameters=params
    )
    try:
        agent.open()
    except SnmpError:
        agent.close()
        raise
    else:
        return agent


if __name__ == '__main__':
    main()
