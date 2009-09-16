# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details. 
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Bit vector manipulation."""

import array

class BitVector(object):
    """
    Represent an octet string as a vector of bits, allowing for easy
    manipulation of the bits.

    Written specifically for manipulating octet strings retrieved by
    SNMP, where the most significant bit represents port 1 on a
    device.  Everything in this class is 0 based though, so index 0 is
    the most significant bit here.
    """
    def __init__(self, octetstring):
        self.vector = array.array("B", octetstring)

    def __str__(self):
        return self.vector.tostring()

    def __len__(self):
        return len(self.vector)*8

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, repr(str(self)))

    def __setitem__(self, posn, val):
        """
        Set the bit in position posn to val.  NOTE: The most
        significant bit is regarded as bit 0 in this context.
        """
        val = val and 1 or 0
        block = posn / 8
        shift = posn & 7
        block_value = self.vector[block]
        if (block_value << shift) & 128 and 1 or 0 != val:
            if val:
                self.vector[block] = block_value | (128 >> shift)
            else:
                self.vector[block] = block_value ^ (128 >> shift)

    def __getitem__(self, posn):
        """
        Get the value of the bit in position posn.  NOTE: The most
        significant bit is regarded as bit 0 in this context.
        """
        if isinstance(posn, slice):
            result = []
            for i in range(*posn.indices(len(self))):
                result.append(self[i])
            return result
        else:
            block = posn / 8
            shift = posn & 7
            return (self.vector[block] << shift) & 128 and 1 or 0

    def to_binary(self):
        """
        Returns a string consisting of 1s and 0s, representing the
        bits in the vector.
        """
        bits = []
        for octet in self.vector:
            bits = bits + [str((octet >> y) & 1) for y in range(8-1, -1, -1)]
        return "".join(bits)
    
    def reverse(self):
        """Reverse the bit pattern."""
        # This is hopelessly ineffective, but it does the job
        reversed_bits = self[-1::-1]
        for index, bit in enumerate(reversed_bits):
            self[index] = bit

    def get_set_bits(self):
        """Return a list of bit numbers that have been set."""
        # This is hopelessly ineffective, but it does the job
        bits = [i for i in range(len(self)) if self[i]]
        return bits
