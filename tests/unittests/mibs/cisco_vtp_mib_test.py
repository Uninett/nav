from mock import Mock, patch
from twisted.internet.defer import succeed
from nav.mibs.cisco_vtp_mib import CiscoVTPMib


def test_it_should_keep_valid_ethernet_vlans():
    result = _get_ethernet_vlan_states(
        {
            (1, 1): {'vtpVlanState': 'operational', 'vtpVlanType': 'ethernet'},
            (1, 4094): {'vtpVlanState': 'operational', 'vtpVlanType': 'ethernet'},
        }
    )
    assert set(result) == {1, 4094}


def test_it_should_drop_out_of_range_vlan_ids():
    # FXOS supervisors have been seen to advertise VLAN index 16777216 (#4245)
    result = _get_ethernet_vlan_states(
        {
            (1, 1): {'vtpVlanState': 'operational', 'vtpVlanType': 'ethernet'},
            (1, 16777216): {'vtpVlanState': 'operational', 'vtpVlanType': 'ethernet'},
            (1, 0): {'vtpVlanState': 'operational', 'vtpVlanType': 'ethernet'},
        }
    )
    assert set(result) == {1}


def _get_ethernet_vlan_states(translated):
    mib = CiscoVTPMib(Mock())
    with (
        patch.object(CiscoVTPMib, 'retrieve_columns', return_value=succeed(translated)),
        patch.object(CiscoVTPMib, 'translate_result', side_effect=lambda x: x),
    ):
        return mib.get_ethernet_vlan_states().result
