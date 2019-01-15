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
"""Implements a BGP4-V2-MIB-JUNIPER MibRetriever w/associated functionality."""

from __future__ import absolute_import

from nav.oidparsers import consume, TypedFixedInetAddress, Unsigned32
from .bgp4_mib import BGP4Mib


class BGP4V2JuniperMib(BGP4Mib):
    """MibRetriever implementation for BGP4-V2-MIB-JUNIPER"""
    from nav.smidumps.bgp4_v2_mib_juniper import MIB as mib
    SUPPORTED_ROOT = 'jnxBgpM2'
    PEERSTATE_COLUMN = 'jnxBgpM2PeerState'
    ADMINSTATUS_COLUMN = 'jnxBgpM2PeerStatus'
    LOCAL_AS_COLUMN = 'jnxBgpM2PeerLocalAs'
    REMOTE_AS_COLUMN = 'jnxBgpM2PeerRemoteAs'
    GLOBAL_LOCAL_AS = 'jnxBgpM2LocalAs'

    @staticmethod
    def _bgp_row_to_remote_ip(row_index):
        _routing_instance, _local_addr, remote_addr = consume(
            row_index,
            Unsigned32, TypedFixedInetAddress, TypedFixedInetAddress)
        return remote_addr
