from django.db.models import Q
from mock import Mock, patch

from nav.ipdevpoll.plugins.lldp import (
    INFO_KEY_LLDP_INFO,
    INFO_VAR_CHASSIS_ID,
    LLDP,
    LLDPNeighbor,
)
from nav.ipdevpoll.storage import ContainerRepository


def test_non_ascii_chassis_id_should_not_crash():
    record = Mock(chassid_id='a\x9enon-ascii')
    plugin = LLDP(None, None, ContainerRepository())
    plugin._store_unidentified(record)


def test_given_local_id_with_nullbytes_then_netbox_from_local_should_not_crash():
    with patch.object(LLDPNeighbor, 'identify'):
        with patch.object(
            LLDPNeighbor, '_netbox_query', return_value=None
        ) as mock_query:
            neighbor = LLDPNeighbor(Mock())
            neighbor._netbox_from_local("somedevice\x00\x00")

            # Verify the first query was called with null bytes stripped
            # (the method makes two queries: first via info_set,
            # then via sysname fallback)
            first_call_q = mock_query.call_args_list[0][0][0]
            expected_q = Q(
                info_set__key=INFO_KEY_LLDP_INFO,
                info_set__variable=INFO_VAR_CHASSIS_ID,
                info_set__value="somedevice",
            )
            assert repr(first_call_q) == repr(expected_q)


def test_given_local_id_with_only_nullbytes_then_netbox_from_local_should_not_crash():
    with patch.object(LLDPNeighbor, 'identify'):
        with patch.object(LLDPNeighbor, '_netbox_query', return_value=None):
            neighbor = LLDPNeighbor(Mock())
            assert not neighbor._netbox_from_local("\x00\x00\x00")
