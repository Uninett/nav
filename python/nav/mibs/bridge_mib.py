import mibretriever

from nav.mibs import reduce_index

class BridgeMib(mibretriever.MibRetriever):
    from nav.smidumps.bridge_mib import MIB as mib

    def get_baseport_ifindex_map(self):
        """Retrieves the mapping between baseport numbers and ifindexes.

        :returns: A dict of the form { baseportnum: ifIndex }

        """
        df = self.retrieve_column('dot1dBasePortIfIndex')
        return df.addCallback(reduce_index)
