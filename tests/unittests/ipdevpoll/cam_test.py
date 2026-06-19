#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Unit tests for the cam ipdevpoll plugin."""

from unittest.mock import Mock, patch

import pytest
from twisted.internet import defer

from nav.ipdevpoll.plugins.cam import Cam


class TestPromoteHybridPorts:
    """Tests for the hybrid port promotion logic in the cam plugin."""

    @pytest.mark.twisted
    async def test_when_no_unmanaged_neighbors_then_it_should_not_modify_accessports(
        self, cam_plugin
    ):
        cam_plugin.linkports = {1: {'aa:bb:cc:dd:ee:01'}}
        cam_plugin.accessports = {2: {'aa:bb:cc:dd:ee:02'}}

        with patch(
            'nav.ipdevpoll.plugins.cam.db.run_in_thread',
            side_effect=lambda func: defer.succeed(func()),
        ):
            with patch.object(
                cam_plugin,
                '_get_unmanaged_neighbor_linkports',
                return_value=set(),
            ):
                await cam_plugin._promote_hybrid_ports()

        assert cam_plugin.accessports == {2: {'aa:bb:cc:dd:ee:02'}}
        assert 1 not in cam_plugin.accessports

    @pytest.mark.twisted
    async def test_when_hybrid_port_exists_then_port_should_appear_in_both_dicts(
        self, cam_plugin
    ):
        cam_plugin.linkports = {1: {'aa:bb:cc:dd:ee:01'}}
        cam_plugin.accessports = {2: {'aa:bb:cc:dd:ee:02'}}

        with patch(
            'nav.ipdevpoll.plugins.cam.db.run_in_thread',
            side_effect=lambda func: defer.succeed(func()),
        ):
            with patch.object(
                cam_plugin,
                '_get_unmanaged_neighbor_linkports',
                return_value={1},
            ):
                await cam_plugin._promote_hybrid_ports()

        assert 1 in cam_plugin.accessports
        assert 1 in cam_plugin.linkports
        assert cam_plugin.accessports[1] == {'aa:bb:cc:dd:ee:01'}

    @pytest.mark.twisted
    async def test_when_flag_is_enabled_then_handle_should_call_promote_hybrid_ports(
        self, cam_plugin
    ):
        cam_plugin.fdb = {1: {'aa:bb:cc:dd:ee:01'}}
        cam_plugin.monitored = {}
        cam_plugin.my_macs = set()

        with (
            patch.object(Cam, '_log_unmanaged_neighbor_macs', True),
            patch.object(
                cam_plugin,
                '_get_dot1q_mac_port_mapping',
                return_value=defer.succeed({1: {'aa:bb:cc:dd:ee:01'}}),
            ),
            patch.object(
                cam_plugin,
                '_get_dot1d_stp_blocking',
                return_value=defer.succeed({}),
            ),
            patch(
                'nav.ipdevpoll.plugins.cam.db.run_in_thread',
                side_effect=lambda func, *a, **kw: defer.succeed(func(*a, **kw)),
            ),
            patch(
                'nav.ipdevpoll.plugins.cam.get_netbox_macs',
                return_value={},
            ),
            patch.object(
                cam_plugin,
                '_promote_hybrid_ports',
                return_value=defer.succeed(None),
            ) as mock_promote,
            patch.object(cam_plugin, '_store_cam_records'),
            patch.object(cam_plugin, '_store_adjacency_candidates'),
        ):
            await cam_plugin.handle()

        mock_promote.assert_called_once()

    @pytest.mark.twisted
    async def test_when_orm_returns_ifindexes_then_promote_should_use_them(
        self, cam_plugin
    ):
        cam_plugin.linkports = {1: {'aa:bb:cc:dd:ee:01'}, 2: {'aa:bb:cc:dd:ee:02'}}
        cam_plugin.accessports = {}

        mock_qs = Mock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.annotate.return_value = mock_qs
        mock_qs.values_list.return_value = [1]

        with (
            patch(
                'nav.ipdevpoll.plugins.cam.db.run_in_thread',
                side_effect=lambda func: defer.succeed(func()),
            ),
            patch(
                'nav.ipdevpoll.plugins.cam.manage.Interface.objects.filter',
                return_value=mock_qs,
            ),
        ):
            await cam_plugin._promote_hybrid_ports()

        assert 1 in cam_plugin.accessports
        assert 2 not in cam_plugin.accessports


@pytest.fixture()
def cam_plugin():
    """Returns a Cam plugin instance with mocked dependencies."""
    netbox = Mock(name='netbox')
    netbox.id = 1
    agent = Mock(name='agent')
    containers = Mock(name='containers')
    # containers.setdefault is used by CamManager.add_sentinel
    containers.setdefault = Mock(return_value={})
    plugin = Cam(netbox, agent, containers)
    return plugin
