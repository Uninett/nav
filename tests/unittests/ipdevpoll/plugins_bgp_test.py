from unittest.mock import Mock, patch

import pytest
import pytest_twisted
from twisted.internet import defer

from nav.mibs.bgp4_mib import BGP4Mib, BgpPeerState, MultiBGP4Mib


def _peer(remote_ip, remote_as):
    return BgpPeerState(
        peer=remote_ip,
        state=6,
        adminstatus=2,
        local_as=64512,
        remote_as=remote_as,
    )


def _make_multi_mib(per_instance_results):
    """
    Builds a MultiBGP4Mib whose fan-out yields one instance per result.
    """
    mib = MultiBGP4Mib(agent_proxy=Mock(), instances=[])
    agents = [
        (mib._base_agent, "instance-%d" % i) for i in range(len(per_instance_results))
    ]
    mib._make_agents = Mock(return_value=iter(agents))
    return mib


class TestMultiBGP4MibGetBgpPeerStates:
    @pytest.mark.twisted
    @pytest_twisted.inlineCallbacks
    def test_it_should_merge_peers_from_all_instances(self):
        instance_results = [
            {"10.0.0.1": _peer("10.0.0.1", 65001)},
            {"10.0.0.2": _peer("10.0.0.2", 65002)},
        ]
        mib = _make_multi_mib(instance_results)

        with patch.object(
            BGP4Mib,
            "get_bgp_peer_states",
            side_effect=[defer.succeed(r) for r in instance_results],
        ):
            merged = yield mib.get_bgp_peer_states()

        assert set(merged) == {"10.0.0.1", "10.0.0.2"}
        assert merged["10.0.0.1"].remote_as == 65001
        assert merged["10.0.0.2"].remote_as == 65002

    @pytest.mark.twisted
    @pytest_twisted.inlineCallbacks
    def test_when_a_peer_appears_in_multiple_instances_it_should_deduplicate(self):
        instance_results = [
            {"10.0.0.1": _peer("10.0.0.1", 65001)},
            {"10.0.0.1": _peer("10.0.0.1", 65999)},
        ]
        mib = _make_multi_mib(instance_results)

        with patch.object(
            BGP4Mib,
            "get_bgp_peer_states",
            side_effect=[defer.succeed(r) for r in instance_results],
        ):
            merged = yield mib.get_bgp_peer_states()

        assert list(merged) == ["10.0.0.1"]
        assert merged["10.0.0.1"].remote_as == 65999
