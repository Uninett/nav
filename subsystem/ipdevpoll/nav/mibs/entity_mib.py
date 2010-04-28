import mibretriever

class EntityMib(mibretriever.MibRetriever):
    from nav.smidumps.entity_mib import MIB as mib

    def retrieve_alternate_bridge_mibs(self):
        """Retrieve a list of alternate bridge mib instances.

        This is accomplished by looking at entLogicalTable.  Returns a
        deferred whose result value is a list of tuples:: 

          (entity_description, community)

        NOTE: Some devices will return entities with the same
        community.  These should effectively be filtered out for
        polling purposes.

        """
        # Define this locally to avoid external overhead
        bridge_mib_oid = [1, 3, 6, 1, 2, 1, 17]
        def bridge_mib_filter(result):
            new_result = [(r['entLogicalDescr'], r['entLogicalCommunity'])
                          for r in result.values()
                          if r['entLogicalType'] == bridge_mib_oid]
            return new_result

        df = self.retrieve_columns([
                'entLogicalDescr',
                'entLogicalType',
                'entLogicalCommunity'
                ])
        df.addCallback(bridge_mib_filter)
        return df
