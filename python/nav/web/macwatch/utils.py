#
# Copyright (C) 2012 Uninett AS
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
"""Utillity functions for macwatch"""

import re

LEGAL_MAC_ADDRESS = re.compile('^[a-fA-F0-9]{12}$')

# Max number of nybbles in a mac-address.
MAC_ADDR_MAX_LEN = 12
# Minimum number of nybbles for a mac-address prefix
MAC_ADDR_MIN_LEN = 6
# Minimum value for a mac-address, used for appending
# zeroes to prefix.
MAC_ADDR_MIN_VAL = '000000000000'


def strip_delimiters(mac_address):
    """Strip delimiters from mac-address.  Legal delimiters
    are '-' and ':'"""
    return re.sub('-', '', re.sub(':', '', mac_address))


def has_legal_values(mac_address):
    """Check if the given mac-addres consists for legal
    hex-numbers.  The mac-address must be stripped for
    delimiters before calling this functiom."""
    if not LEGAL_MAC_ADDRESS.match(mac_address):
        return False
    return True


def add_zeros_to_mac_addr(mac_address):
    """Add zeroes at the end of a mac-address if the given
    mac-address has less than 6 octets.
    The mac-address given as parameter will not get checked
    if it only contains legal hex-numbers."""
    prefix_len = len(mac_address)
    if prefix_len < MAC_ADDR_MAX_LEN:
        mac_address += MAC_ADDR_MIN_VAL[prefix_len:]
    return mac_address
