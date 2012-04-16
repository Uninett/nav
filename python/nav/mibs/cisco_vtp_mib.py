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

    @defer.inlineCallbacks
    def get_vlan_states(self):
        "Retrieves the state of each VLAN on the device"
        states = yield self.retrieve_columns(
            ['vtpVlanState']).addCallback(self.translate_result)

        result = dict((vlan, row['vtpVlanState'])
                      for (_domain, vlan), row in states.items())
        defer.returnValue(result)

    @defer.inlineCallbacks
    def get_operational_vlans(self):
        "Retrieves a set of operational VLANs on this device"
        states = yield self.get_vlan_states()
        defer.returnValue(set(vlan for vlan, state in states.items()
                              if state == 'operational'))

    @defer.inlineCallbacks
    def retrieve_alternate_bridge_mibs(self):
        """Retrieve a list of alternate bridge mib instances.

        :returns: A list of (descr, community) tuples for each operational
                  VLAN on this device.

        """
        vlans = yield self.get_operational_vlans()
        community = self.agent_proxy.community
        defer.returnValue([("vlan%s" % vlan, "%s@%s" % (community, vlan))
                           for vlan in vlans])
