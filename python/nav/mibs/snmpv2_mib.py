from nav.oids import OID
import mibretriever

class Snmpv2Mib(mibretriever.MibRetriever):
    from nav.smidumps.snmpv2_mib import MIB as mib

    def _get_sysvariable(self, var):
        """Retrieves a system variable of the first agent instance.

        Will first try get-next on {var}, then fall back to getting
        {var}.0 on failure.  This is to work around SNMP bugs observed in
        some agents  (Weathergoose).

        """
        oid = str(self.nodes[var].oid + OID('0'))

        def format_get_result(result):
            if oid in result:
                return result[oid]

        def format_getnext_result(result):
            if result and hasattr(result, 'values'):
                return result.values()[0]
            else:
                raise ValueError("invalid result value", result)

        def use_get(failure):
            df = self.agent_proxy.get([oid])
            df.addCallback(format_get_result)
            return df

        df = self.retrieve_column(var)
        df.addCallback(format_getnext_result)
        df.addErrback(use_get)
        return df

    def get_sysObjectID(self):
        """Retrieves the sysObjectID of the first agent instance."""
        return self._get_sysvariable('sysObjectID')

    def get_sysDescr(self):
        """Retrieves the sysDescr of the first agent instance."""
        return self._get_sysvariable('sysDescr')
