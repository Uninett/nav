#!/usr/bin/env python
# -*- testargs: -h -*-
#
# Copyright (C) 2014, 2019 Uninett AS
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
A command line program to output an entity hierarchy graph from a device's
ENTITY-MIB::entPhysicalTable.
"""

import sys
import argparse

import asciitree
import networkx

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from nav.util import is_valid_ip
from nav.ipdevpoll.snmp.common import SnmpError, SNMPParameters
from nav.ipdevpoll.snmp import AgentProxy, snmpprotocol
from nav.mibs.entity_mib import EntityMib
from nav.models.manage import Netbox

from twisted.internet import reactor, defer

_exit_code = 0
TIMEOUT = SNMPParameters.DEFAULT_TIMEOUT


def main():
    """Main program"""
    options = parse_args()

    if options.device:
        reactor.callWhenRunning(
            reactor_main, options.device, options.port, options.timeout
        )
        reactor.run()
        sys.exit(_exit_code)


def reactor_main(box, portnumber, timeout=TIMEOUT):
    """The main function to start in the event reactor"""
    header = "{sysname} ({ip}:{port})".format(port=portnumber, **vars(box))
    print(header)
    print("-" * len(header))
    df = defer.ensureDeferred(collect_entities(box, portnumber, timeout))
    df.addCallback(make_graph, box)
    df.addCallback(print_graph)
    df.addErrback(failure_handler)
    df.addBoth(endit)
    return df


async def collect_entities(netbox, portnumber, timeout=TIMEOUT):
    """Collects the entPhysicalTable"""
    agent = _create_agentproxy(netbox, portnumber, timeout)
    if not agent:
        return None

    mib = EntityMib(agent)
    result = await mib.get_entity_physical_table()
    return result


def make_graph(entities, netbox):
    """Makes a NetworkX DiGraph from the entPhysicalTable result"""
    graph = networkx.DiGraph(name="%s entPhysicalTable" % netbox)
    for index, entity in entities.items():
        container = entity.get('entPhysicalContainedIn', None)
        if container and container in entities:
            graph.add_edge(index, container)
        only_string_data = {k: v for k, v in entity.items() if isinstance(k, str)}
        graph.add_node(index, **only_string_data)
    return graph


def print_graph(graph):
    """Prints an ASCII representation of a NetworkX DiGraph tree to stdout"""
    traversal = GraphTraversal(graph)
    for root in traversal.get_roots():
        output = asciitree.LeftAligned(traverse=traversal)(root)
        print(output)
    return graph


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
        description="Outputs entity hierarchy graph from a device's "
        "ENTITY-MIB::entPhysicalTable response",
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
                ", ".join(box for box in netbox),
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


def _create_agentproxy(netbox, portnumber, timeout=TIMEOUT):
    params = SNMPParameters.factory(netbox, timeout=timeout)
    if not params:
        return

    port = snmpprotocol.port()
    agent = AgentProxy(
        netbox.ip, portnumber, protocol=port.protocol, snmp_parameters=params
    )
    try:
        agent.open()
    except SnmpError:
        agent.close()
        raise
    else:
        return agent


class GraphTraversal(asciitree.Traversal):
    def __init__(self, graph):
        super(GraphTraversal, self).__init__()
        self.graph = graph

    def get_children(self, node):
        return [u for u, v in self.graph.in_edges(node)]

    def get_text(self, node):
        ent = self.graph.nodes[node]
        labels = [
            ent.get('entPhysicalName'),
            "[{}]".format(ent.get('entPhysicalClass')),
        ]
        serial = ent.get('entPhysicalSerialNum', None)
        if serial:
            labels.append('({})'.format(serial))

        software = ent.get('entPhysicalSoftwareRev', None)
        if software:
            labels.append('(sw={})'.format(software))

        return " ".join(labels)

    def get_roots(self):
        return [n for n, d in self.graph.out_degree() if d == 0]


if __name__ == '__main__':
    main()
