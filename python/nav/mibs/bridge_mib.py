#
# Copyright (C) 2009, 2011, 2012, 2017, 2018 Uninett AS
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
"""Implements a BRIDGE-MIB MibRetriever and associated functionality."""

from twisted.internet import defer

from nav.smidumps import get_mib
from . import mibretriever, reduce_index


class BridgeMib(mibretriever.MibRetriever):
    """MibRetriever implementation for BRIDGE-MIB"""

    mib = get_mib('BRIDGE-MIB')

    def get_baseport_ifindex_map(self):
        """Retrieves the mapping between baseport numbers and ifindexes.

        :returns: A dict of the form { baseportnum: ifIndex }

        """
        df = self.retrieve_column('dot1dBasePortIfIndex')
        return df.addCallback(reduce_index)

    @defer.inlineCallbacks
    def get_base_bridge_address(self):
        addr = yield self.get_next('dot1dBaseBridgeAddress')
        return addr

    @defer.inlineCallbacks
    def get_forwarding_database(self):
        """Retrieves the forwarding database of the device."""
        columns = yield self.retrieve_columns(['dot1dTpFdbPort', 'dot1dTpFdbStatus'])
        columns = self.translate_result(columns)
        valid = (
            row
            for row in columns.values()
            if row['dot1dTpFdbStatus'] not in ('self', 'invalid')
        )
        result = []
        for row in valid:
            mac = row[0]
            mac = ':'.join("%02x" % o for o in mac[-6:])
            port = row['dot1dTpFdbPort']
            result.append((mac, port))
        return result

    @defer.inlineCallbacks
    def get_stp_blocking_ports(self):
        """Retrieves a list of numbers of STP blocking ports"""
        states = yield self.__get_stp_port_states()
        blocked = [port for port, state in states if state == 'blocking']
        return blocked

    @defer.inlineCallbacks
    def get_stp_port_states(self):
        """Retrieves the spanning tree port states of the device."""
        states = yield self.retrieve_columns(['dot1dStpPortState'])
        states = reduce_index(self.translate_result(states))
        result = [(k, v['dot1dStpPortState']) for k, v in states.items()]
        return result

    __get_stp_port_states = get_stp_port_states


class MultiBridgeMib(BridgeMib, mibretriever.MultiMibMixIn):
    def get_baseport_ifindex_map(self):
        method = super(MultiBridgeMib, self).get_baseport_ifindex_map
        return self._multiquery(method)

    def get_forwarding_database(self):
        method = super(MultiBridgeMib, self).get_forwarding_database
        return self._multiquery(method)

    def get_stp_blocking_ports(self):
        def _integrator(results):
            endresult = []
            for descr, ports in results:
                if ports is not None:
                    for port in ports:
                        endresult.append((port, descr))
            return endresult

        method = super(MultiBridgeMib, self).get_stp_blocking_ports
        return self._multiquery(method, integrator=_integrator)

    def get_stp_port_states(self):
        def _integrator(results):
            endresult = []
            for descr, result in results:
                if result is not None:
                    for port, state in result:
                        endresult.append((port, descr, state))
            return endresult

        method = super(MultiBridgeMib, self).get_stp_port_states
        return self._multiquery(method, integrator=_integrator)
