import sys
from unittest.mock import Mock

from nav.enterprise.ids import (
    VENDOR_ID_ARISTA_NETWORKS_INC_FORMERLY_ARASTRA_INC,
    VENDOR_ID_CISCOSYSTEMS,
)
from nav.ipdevpoll.plugins.bgp import BGP
from nav.ipdevpoll.storage import ContainerRepository
from nav.mibs.bgp4_mib import BGP4Mib, MultiBGP4Mib, _dict_integrator
from nav.mibs.mibretriever import MultiMibMixIn


sys.modules["psycopg2"] = Mock()
sys.modules["psycopg2.extensions"] = Mock()
sys.modules["psycopg2.extras"] = Mock()


class TestDictIntegrator:
    def test_should_merge_dicts_from_all_instances(self):
        results = [
            ('vrf-a', {'10.0.0.1': 'peer-a'}),
            ('vrf-b', {'10.0.0.2': 'peer-b'}),
        ]
        merged = _dict_integrator(results)
        assert merged == {'10.0.0.1': 'peer-a', '10.0.0.2': 'peer-b'}

    def test_should_deduplicate_keys_across_instances(self):
        results = [
            ('vrf-a', {'10.0.0.1': 'first'}),
            ('vrf-b', {'10.0.0.1': 'second'}),
        ]
        merged = _dict_integrator(results)
        assert merged == {'10.0.0.1': 'second'}

    def test_should_handle_empty_or_none_results(self):
        results = [
            ('vrf-a', None),
            ('vrf-b', {}),
            ('vrf-c', {'10.0.0.1': 'peer'}),
        ]
        merged = _dict_integrator(results)
        assert merged == {'10.0.0.1': 'peer'}

    def test_empty_input_returns_empty_dict(self):
        assert _dict_integrator([]) == {}


class TestMultiBGP4Mib:
    def test_should_be_subclass_of_bgp4mib(self):
        assert issubclass(MultiBGP4Mib, BGP4Mib)

    def test_should_be_subclass_of_multimibmixin(self):
        assert issubclass(MultiBGP4Mib, MultiMibMixIn)


def _make_bgp_plugin(enterprise_id):
    netbox = Mock()
    if enterprise_id is None:
        netbox.type = None
    else:
        netbox.type.get_enterprise_id.return_value = enterprise_id
    return BGP(netbox, agent=None, containers=ContainerRepository())


class TestIsArista:
    def test_returns_true_for_arista_device(self):
        plugin = _make_bgp_plugin(
            VENDOR_ID_ARISTA_NETWORKS_INC_FORMERLY_ARASTRA_INC
        )
        assert plugin.is_arista()

    def test_returns_false_for_cisco_device(self):
        plugin = _make_bgp_plugin(VENDOR_ID_CISCOSYSTEMS)
        assert not plugin.is_arista()

    def test_returns_false_when_netbox_has_no_type(self):
        plugin = _make_bgp_plugin(None)
        assert not plugin.is_arista()
