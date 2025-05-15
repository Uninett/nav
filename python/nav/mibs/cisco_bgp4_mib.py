#
# Copyright (C) 2017 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
#
"""Implements a CISCO-BGP4-MIB MibRetriever w/associated functionality."""

from nav.oidparsers import consume, TypedInetAddress
from nav.smidumps import get_mib
from .bgp4_mib import BGP4Mib


class CiscoBGP4Mib(BGP4Mib):
    """MibRetriever implementation for CISCO-BGP4-MIB"""

    mib = get_mib('CISCO-BGP4-MIB')
    SUPPORTED_ROOT = 'cbgpPeer2Table'
    PEERSTATE_COLUMN = 'cbgpPeer2State'
    ADMINSTATUS_COLUMN = 'cbgpPeer2AdminStatus'
    LOCAL_AS_COLUMN = 'cbgpPeer2LocalAs'
    REMOTE_AS_COLUMN = 'cbgpPeer2RemoteAs'
    LOCAL_AS_OBJECT = 'cbgpLocalAs'

    @staticmethod
    def _bgp_row_to_remote_ip(row_index):
        (remote_addr,) = consume(row_index, TypedInetAddress)
        return remote_addr
