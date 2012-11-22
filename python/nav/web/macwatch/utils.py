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

LEGAL_MAC_ADDRESS = re.compile('^[a-fA-F0-9]{12}$')
MAC_ADDR_MAX_LEN = 12
MAC_ADDR_MIN_LEN = 6

def add_zeros_to_mac_addr(mac_address):
    """Add zeroes at the end of a mac-address if the given mac-address
    has less than 6 octets.
    The mac-address must contain at least 3 octets as a vendor-prefix."""
    result_address = re.sub('-', '', re.sub(':', '', mac_address))
    prefix_len = len(result_address)
    if prefix_len < MAC_ADDR_MIN_LEN or prefix_len > MAC_ADDR_MAX_LEN:
        return (mac_address, 0)
    if prefix_len < MAC_ADDR_MAX_LEN:
        idx = prefix_len
        while idx < MAC_ADDR_MAX_LEN:
            result_address += '0'
            idx += 1
    if not LEGAL_MAC_ADDRESS.match(result_address):
        return (mac_address, 0)
    return (result_address, prefix_len)

