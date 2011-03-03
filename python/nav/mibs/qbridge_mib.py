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
"""Implements a Q-BRIDGE-MIB MibRetriever and associated functionality."""

import mibretriever
import nav.bitvector

class QBridgeMib(mibretriever.MibRetriever):
    from nav.smidumps.qbridge_mib import MIB as mib

class PortList(str):
    """Represent an octet string, as defined by the PortList syntax of
    the Q-BRIDGE-MIB.

    Offers conveniences such as subtracting one PortList from another,
    and retrieving a list of port numbers represented by a PortList
    octet string.

    """

    def __sub__(self, other):
        new_ints = [ord(char) - ord(other[index]) 
                    for index, char in enumerate(self)]
        return PortList(''.join(chr(i) for i in new_ints))
    
    def get_ports(self):
        """Return a list of port numbers represented by this PortList."""
        vector = nav.bitvector.BitVector(self)
        # a bitvector is indexed from 0, but ports are indexed from 1
        ports = [b+1 for b in vector.get_set_bits()]
        return ports
