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
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""ipdevpoll plugin to collect bridge data.

This plugin doesn't do much except find baseport numbers for switch
ports, using the BRIDGE-MIB.  The plugin also supports multiple
BRIDGE-MIB instances if they are listed as logical entities in
ENTITY-MIB.

"""

from twisted.internet import defer
from twisted.python.failure import Failure
from twistedsnmp import agentproxy

from nav.mibs.bridge_mib import BridgeMib
from nav.mibs.entity_mib import EntityMib
from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage, shadows

class Bridge(Plugin):
    @classmethod
    def can_handle(cls, netbox):
        return True

    def handle(self):
        self.logger.debug("Collecting bridge data")
        self.entity = EntityMib(self.agent)
        self.baseports = {}

        df = self.entity.retrieve_alternate_bridge_mibs()
        df.addCallback(self._prune_bridge_mib_list)
        df.addCallback(self._query_baseports)
        df.addErrback(self._error)

        return df

    def _error(self, failure):
        """Errback for SNMP failures."""
        if failure.check(defer.TimeoutError):
            # Transform TimeoutErrors to something else
            self.logger.error(failure.getErrorMessage())
            # Report this failure to the waiting plugin manager (RunHandler)
            exc = FatalPluginError("Cannot continue due to device timeouts")
            failure = Failure(exc)
        return failure

    def _get_alternate_agent(self, community):
        """Create an alternative Agent Proxy for our host.

        Return value is an AgentProxy object created with the same
        parameters as the controlling job handler's AgentProxy, but
        with a different community.

        """
        old_agent = self.agent
        agent = agentproxy.AgentProxy(
            old_agent.ip, old_agent.port,
            community=community,
            snmpVersion = old_agent.snmpVersion,
            protocol = old_agent.protocol)
        return agent

    def _prune_bridge_mib_list(self, result):
        """Prune the list of alternate bridge mib instances.

        Any instance with a previously known community is removed from
        the result list.

        """
        self.logger.debug("Alternate BRIDGE-MIB instances: %r", result)

        seen_communities = set(self.agent.community)
        new_result = []

        for descr, community in result:
            if community not in seen_communities:
                new_result.append((descr, community))
                seen_communities.add(community)

        return new_result
        

    def _query_baseports(self, bridgemibs):
        """Set up a chain to query each of the known BRIDGE-MIB instances."""

        self.logger.debug("Querying the following alternative instances: %r",
                          [b[0] for b in bridgemibs])

        # Set up a bunch of instances to poll
        instances = [ (BridgeMib(self.agent), None) ]
        for descr, community in bridgemibs:
            agent = self._get_alternate_agent(community)
            mib = BridgeMib(agent)
            instances.append((mib, descr))
        
        instances = iter(instances)
        df = self._query_next_instance(None, instances)
        return df

    def _query_next_instance(self, result, instances):
        """Callback to be chained for each BRIDGE-MIB instance to query.

        This callback does the actual retrieval of the baseport list
        for a single BRIDGE-MIB instance, adds the intermediate
        results to the final set of baseports, and chains itself to
        collect from the next instance.

        """
        # Append any new result to the set of existing results
        if result:
            if not self.baseports:
                self.baseports = result
            else:
                self.baseports.update(result)

        try:
            bridgemib, descr = instances.next()
            self.logger.debug("Now querying %r", descr)
        except StopIteration:
            return self._set_port_numbers(self.baseports)

        # Add the next bridge mib instance to the chain
        df = bridgemib.retrieve_column('dot1dBasePortIfIndex')
        df.addCallback(self._query_next_instance, instances)
        return df

    def _set_port_numbers(self, result):
        """Process the list of collected base ports and set port numbers."""

        self.logger.debug("Found %d base (switch) ports: %r", 
                          len(result),
                          [portnum[0] for portnum in result.keys()])

        # Now save stuff to containers and pass the list of containers
        # to the next callback
        for portnum, ifindex in result.items():
            # The index is a single integer
            portnum = portnum[0]
            interface = self.containers.factory(ifindex, shadows.Interface)
            interface.baseport = portnum

        return result
    
