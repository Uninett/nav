# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Utility functions for ipdevpoll."""

def binary_mac_to_hex(binary_mac):
    """Convert a binary string MAC address to hex string."""
    if binary_mac:
        return ":".join("%02x" % ord(x) for x in binary_mac)

def truncate_mac(mac):
    """Takes a MAC address on the form xx:xx:xx... of any length and returns
    the first 6 parts.
    """
    parts = mac.split(':')
    if len(parts) > 6:
        mac = ':'.join(parts[:6])
    return mac
