#!/usr/bin/env python
# -*- testargs: .1.3.6.1.2.1.1.2 -*-
#
# Copyright (C) 2014 Uninett AS
# Copyright (C) 2023 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
A command line program to verify support for SNMP subtrees in sets of
NAV-monitored devices.
"""

import platform
import sys
from itertools import cycle
from argparse import ArgumentParser

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

if platform.system() == "Linux":
    from nav.ipdevpoll.epollreactor2 import install

    install()

from nav.ipdevpoll.snmp.common import SNMPParameters, SnmpError
from nav.models.manage import Netbox, ManagementProfile
from nav.ipdevpoll.snmp import snmpprotocol, AgentProxy
from nav.oids import OID

from twisted.internet import reactor, defer, task


def main():
    """Main program"""
    options = parse_args()

    sysnames = [n.strip() for n in sys.stdin.readlines()]
    if sysnames:
        boxes = Netbox.objects.filter(sysname__in=sysnames)
    else:
        boxes = Netbox.objects.filter(
            profiles__protocol=ManagementProfile.PROTOCOL_SNMP
        )

    if boxes:
        reactor.callWhenRunning(reactor_main, list(boxes), options.baseoid)
        reactor.run()


def reactor_main(boxes, baseoid):
    """The main function to start in the event reactor"""
    df = parallel(boxes, 50, verify, baseoid)
    return df.addCallback(endit)


async def verify(netbox, oid):
    """Verifies a GETNEXT response from below the oid subtree"""
    agent = _create_agentproxy(netbox)
    if not agent:
        return False

    result = await agent.walk(str(oid))
    agent.close()

    if hasattr(result, 'items'):
        result = result.items()
    for key, _value in result:
        if oid.is_a_prefix_of(key):
            print(netbox.sysname)
            return True
    return False


def endit(_result):
    """Stops the reactor"""
    reactor.stop()


def parse_args():
    """Parses the command line arguments"""
    parser = ArgumentParser(
        description="Verifies SNMP sub-tree support on a set of NAV-monitored devices",
        usage="%(prog)s baseoid < sysnames.txt",
        epilog=(
            "Given the root of an SNMP MIB module, a bunch of devices can "
            "be queried in parallel whether they have any objects below "
            "the given BASEOID - effectively verifying MIB support in "
            "these devices."
        ),
    )
    parser.add_argument(
        'baseoid',
        type=OID,
        help="The base OID for which a GETNEXT operation will be performed",
    )
    return parser.parse_args()


def parallel(iterable, count, func, *args, **kwargs):
    """Limits the number of parallel requests to count"""
    coop = task.Cooperator()
    work = (defer.ensureDeferred(func(elem, *args, **kwargs)) for elem in iterable)
    return defer.DeferredList(
        [coop.coiterate(work) for _ in range(count)], consumeErrors=True
    )


_ports = cycle([snmpprotocol.port() for _ in range(50)])


def _create_agentproxy(netbox):
    params = SNMPParameters.factory(netbox)
    if not params:
        return

    port = next(_ports)
    agent = AgentProxy(netbox.ip, 161, protocol=port.protocol, snmp_parameters=params)
    try:
        agent.open()
    except SnmpError:
        agent.close()
        raise
    else:
        return agent


if __name__ == '__main__':
    main()
