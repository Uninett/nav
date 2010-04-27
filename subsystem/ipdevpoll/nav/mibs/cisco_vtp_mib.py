from twisted.internet import defer

from nav.bitvector import BitVector
import mibretriever

class CiscoVTPMib(mibretriever.MibRetriever):
    from nav.smidumps.cisco_vtp_mib import MIB as mib

    @defer.deferredGenerator
    def get_trunk_native_vlans(self):
        """Get a mapping of the native VLANs of trunk ports."""
        dw = defer.waitForDeferred(
            self.retrieve_columns((
                    'vlanTrunkPortNativeVlan',
                    'vlanTrunkPortDynamicStatus',
                    ))
            )
        yield dw
        trunkports = self.translate_result(dw.getResult())
        
        result = dict([(index[0], row['vlanTrunkPortNativeVlan'])
                       for index, row in trunkports.items()
                       if row['vlanTrunkPortDynamicStatus'] == 'trunking'])
        yield result


    @defer.deferredGenerator
    def get_trunk_enabled_vlans(self, as_bitvector=False):
        """Get a list of enabled VLANs for each trunk port.

        If as_bitvector=True, the result will be a raw BitVector object.

        """

        def get_vlan_list(row):
            concatenated_bits = ''
            # There is no point in concatening more bitstrings if one of them
            # are empty, that would just produced a skewed result.
            for column in ('vlanTrunkPortVlansEnabled',
                           'vlanTrunkPortVlansEnabled2k',
                           'vlanTrunkPortVlansEnabled3k',
                           'vlanTrunkPortVlansEnabled4k'):
                if row[column]:
                    concatenated_bits += row[column]
                else:
                    break

            enabled = BitVector(concatenated_bits)
            return as_bitvector and enabled or enabled.get_set_bits()

        dw = defer.waitForDeferred(
            self.retrieve_columns((
                    'vlanTrunkPortVlansEnabled',
                    'vlanTrunkPortDynamicStatus',
                    'vlanTrunkPortVlansEnabled2k',
                    'vlanTrunkPortVlansEnabled3k',
                    'vlanTrunkPortVlansEnabled4k',
                    ))
            )
        yield dw
        trunkports = self.translate_result(dw.getResult())

        result = dict([(index[0], get_vlan_list(row))
                       for index, row in trunkports.items()
                       if row['vlanTrunkPortDynamicStatus'] == 'trunking'])
        yield result
