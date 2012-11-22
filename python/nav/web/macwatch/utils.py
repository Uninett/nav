#
# Copyright (C) 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Utillity functions for macwatch"""

import re

LEGAL_MAC_ADDRESS = re.compile('^[a-fA-F0-9]{2}(:[a-fA-F0-9]{2}){1,5}$')
MAC_ADDR_MAX_OCTETS = 6


def add_zeros_to_mac_addr(mac_address):
    """Add zeroes at the end of a mac-address.  The mac-address
    must separate octets with colon (:).
    The mac-address must contain at least 2 octets in the front,
    and must not be ended with a colon (:)."""
    if not LEGAL_MAC_ADDRESS.match(mac_address):
        return mac_address
    split_address = re.split(':', mac_address)
    idx = len(split_address)
    result_address = mac_address
    while idx < MAC_ADDR_MAX_OCTETS:
        result_address += ':00'
        idx += 1
    return result_address

