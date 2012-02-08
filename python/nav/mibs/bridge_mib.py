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
            mac =  ':'.join(["%02x" % o for o in row[0]])
            port = row['dot1dTpFdbPort']
            result.append((mac, port))
        defer.returnValue(result)
class MultiBridgeMib(BridgeMib, mibretriever.MultiMibMixIn):
    def get_baseport_ifindex_map(self):
        method = super(MultiBridgeMib, self).get_baseport_ifindex_map
        return self._multiquery(method)

    def get_forwarding_database(self):
        method = super(MultiBridgeMib, self).get_forwarding_database
        return self._multiquery(method)
