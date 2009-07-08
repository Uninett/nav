# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details. 
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""MIB parsing and MIB-aware data retrieval."""

import os
import mibretriever

class Snmpv2Mib(mibretriever.MibRetriever):
    from nav.smidumps.snmpv2_mib import MIB as mib

class IfMib(mibretriever.MibRetriever):
    from nav.smidumps.if_mib import MIB as mib

class IpMib(mibretriever.MibRetriever):
    from nav.smidumps.ip_mib import MIB as mib

class EntityMib(mibretriever.MibRetriever):
    from nav.smidumps.entity_mib import MIB as mib

class QBridgeMib(mibretriever.MibRetriever):
    from nav.smidumps.qbridge_mib import MIB as mib

class BridgeMib(mibretriever.MibRetriever):
    from nav.smidumps.bridge_mib import MIB as mib

class CiscoVTPMib(mibretriever.MibRetriever):
    from nav.smidumps.cisco_vtp_mib import MIB as mib

modules = mibretriever.MibRetrieverMaker.modules

def test(host, community='public', mib=IfMib, tablename='ifTable'):
    import logging
    global final_result
    from twisted.internet import reactor, defer, task
    from twistedsnmp import snmpprotocol, agentproxy

    #logging.basicConfig()
    #logging.getLogger('').setLevel(logging.DEBUG)

    port = snmpprotocol.port()
    agent = agentproxy.AgentProxy(
        host, 161,
        community = community,
        snmpVersion = 'v2c',
        protocol = port.protocol,
        )

    retriever = mib(agent)

    def printResult(result):
        import pprint
        pprint.pprint(result)
        global final_result
        final_result = result
        reactor.callLater(0, reactor.stop)

    def runner():
        deferred = retriever.retrieve_table(tablename)
        deferred.addCallback(printResult)

    reactor.callWhenRunning(runner)
    reactor.run()

