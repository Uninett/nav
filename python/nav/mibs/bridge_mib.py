import mibretriever

from twisted.internet import defer

from nav.mibs import reduce_index

class BridgeMib(mibretriever.MibRetriever):
    from nav.smidumps.bridge_mib import MIB as mib

    def get_baseport_ifindex_map(self):
        """Retrieves the mapping between baseport numbers and ifindexes.

        :returns: A dict of the form { baseportnum: ifIndex }

        """
        df = self.retrieve_column('dot1dBasePortIfIndex')
        return df.addCallback(reduce_index)

    @defer.inlineCallbacks
    def get_forwarding_database(self):
        """Retrieves the forwarding database of the device."""
        columns = yield self.retrieve_columns(['dot1dTpFdbPort',
                                               'dot1dTpFdbStatus'])
        columns = self.translate_result(columns)
        learned = (row for row in columns.values()
                   if row['dot1dTpFdbStatus'] == 'learned')
        result = []
        for row in learned:
            mac = row[0]
            mac =  ':'.join("%02x" % o for o in mac[-6:])
            port = row['dot1dTpFdbPort']
            result.append((mac, port))
        defer.returnValue(result)

    @defer.inlineCallbacks
    def get_stp_blocking_ports(self):
        """Retrieves a list of numbers of STP blocking ports"""
        states = yield self.__get_stp_port_states()
        blocked = [port for port, state in states if state == 'blocking']
        defer.returnValue(blocked)

    @defer.inlineCallbacks
    def get_stp_port_states(self):
        """Retrieves the spanning tree port states of the device."""
        states = yield self.retrieve_columns(['dot1dStpPortState'])
        states = reduce_index(self.translate_result(states))
        result = [(k, v['dot1dStpPortState']) for k, v in states.items()]
        defer.returnValue(result)

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

