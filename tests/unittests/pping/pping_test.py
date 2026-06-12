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
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#


"""Unit tests for the pping service"""

from unittest import TestCase
from unittest.mock import Mock, patch

from nav.bin.pping import Pinger
from nav.statemon.circbuf import CircBuf
from nav.statemon.netbox import Netbox


class TestPingerUpdateHostList(TestCase):
    def setUp(self):
        mock_conf = Mock()
        mock_conf.get = lambda key, default=None: {
            'checkinterval': '60',
            'nrping': '3',
            'groups_included': '',
            'groups_excluded': '',
        }.get(key, default)

        with (
            patch('nav.bin.pping.config.pingconf', return_value=mock_conf),
            patch('nav.bin.pping.init_generic_logging'),
            patch('nav.bin.pping.db.db', return_value=Mock()),
            patch('nav.bin.pping.megaping.MegaPing', return_value=Mock()),
        ):
            self.pinger = Pinger(socket=None, foreground=True)

    def _seed(self, netboxid, ip, up='y'):
        netbox = Netbox(netboxid, 'router', ip, up)
        self.pinger.netboxmap[netboxid] = netbox
        self.pinger.ip_to_netboxid[ip] = netboxid
        buf = CircBuf(self.pinger._nrping)
        self.pinger.replies[netboxid] = buf
        if up != 'y':
            buf.reset_all_to(-1)
            self.pinger.down.append(netboxid)

    def _run(self, hosts):
        self.pinger.db.hosts_to_ping = Mock(return_value=hosts)
        self.pinger.pinger.set_hosts = Mock()
        self.pinger.update_host_list()

    def test_given_new_netbox_marked_up_in_db_then_it_should_not_be_in_down(self):
        self._run([(1, 'host1', '10.0.0.1', 'y')])
        assert 1 not in self.pinger.down

    def test_given_new_netbox_marked_down_in_db_then_it_should_be_in_down_with_replies_reset(  # noqa: E501
        self,
    ):
        self._run([(1, 'host1', '10.0.0.1', 'n')])
        assert 1 in self.pinger.down
        assert self.pinger.replies[1][:3] == [-1, -1, -1]

    def test_given_known_netbox_down_in_db_but_up_internally_then_it_should_be_added_to_down_with_replies_reset(  # noqa: E501
        self,
    ):
        self._seed(1, '10.0.0.1', up='y')
        self._run([(1, 'host1', '10.0.0.1', 'n')])
        assert 1 in self.pinger.down
        assert self.pinger.replies[1][:3] == [-1, -1, -1]

    def test_given_known_netbox_down_then_it_should_not_be_duplicated(self):
        self._seed(1, '10.0.0.1', up='n')
        self._run([(1, 'host1', '10.0.0.1', 'n')])
        assert self.pinger.down.count(1) == 1

    def test_given_known_netbox_down_internally_but_db_says_up_then_it_should_stay_in_down(  # noqa: E501
        self,
    ):
        self._seed(1, '10.0.0.1', up='n')
        self._run([(1, 'host1', '10.0.0.1', 'y')])
        assert 1 in self.pinger.down

    def test_given_known_netbox_up_and_up_in_db_then_it_should_not_be_in_down(self):
        self._seed(1, '10.0.0.1', up='y')
        self._run([(1, 'host1', '10.0.0.1', 'y')])
        assert 1 not in self.pinger.down
