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
        oid = self.nodes[var].oid
        direct_oid = oid + OID('0')

        def format_get_result(result):
            if direct_oid in result:
                return result[direct_oid]

        def format_getnext_result(result):
            if result and hasattr(result, 'values'):
                return result.values()[0]
            else:
                raise ValueError("invalid result value", result)

        def format_result_keys(result):
            return dict((OID(k), v) for k, v in result.items())

        def use_get(failure):
            df = self.agent_proxy.get([str(direct_oid)])
            df.addCallback(format_result_keys)
            df.addCallback(format_get_result)
            return df

        df = self.agent_proxy.walk(str(oid))
        df.addCallback(format_getnext_result)
        df.addErrback(use_get)
        return df

    def get_sysObjectID(self):
        """Retrieves the sysObjectID of the first agent instance."""
        return self._get_sysvariable('sysObjectID')

    def get_sysDescr(self):
        """Retrieves the sysDescr of the first agent instance."""
        return self._get_sysvariable('sysDescr')
