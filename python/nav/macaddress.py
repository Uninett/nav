#
# Copyright 2013 (C) Uninett AS
# Copyright (C) 2022 Sikt
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
"""MAC address manipulation.

MAC is a Media Access Control address. It may also be known as an Ethernet
hardware address (EHA), hardware address or physical address.

The standard (IEEE 802) format for printing MAC-48 addresses in human-
friendly form is six groups of two hexadecimal digits, separated by hyphens
(-) or colons (:), in transmission order (e.g. 01-23-45-67-89-ab or
01:23:45:67:89:ab). This form is also commonly used for EUI-64. Anotqher
convention used by networking equipment uses three groups of four hexadecimal
digits separated by dots (.) (e.g. 0123.4567.89ab), again in transmission
order.

"""

import re
import string

# A range of left shift values for the 6 bytes in a MAC address
_SHIFT_RANGE = tuple(x * 8 for x in reversed(range(6)))
# Legal delimiters and the number of nybbles between them.
DELIMS_AND_STEPS = {
    '.': 4,
    ':': 2,
    '-': 2,
}
# Only these characters are allowed in a MacAddress after delimiters have
# been stripped.
MAC_ADDRESS_PATTERN = re.compile('^[a-fA-F0-9]+$')
# Number of nybbles in a valid mac-address.
MAC_ADDR_NYBBLES = 12
# Obviously number of bits for a nybble.
NUM_BITS_IN_NYBBLE = 4


class MacAddress(object):
    """A representation of a single MAC address"""

    # Default delimiter for a mac-address as a string.
    DEFAULT_DELIM = ':'
    # Maximum value for a mac-address when all bits are set.
    MAX_MAC_ADDR_VALUE = 0xFFFFFFFFFFFF
    # Strip for delimiters and test against this pattern.
    MAC_ADDRESS_PATTERN = re.compile('^[a-fA-F0-9]{6,12}$')
    # To hold the value for a mac-address as an int.
    _addr = None

    def __init__(self, addr):
        if isinstance(addr, MacAddress):
            self._addr = addr._addr
        elif isinstance(addr, int):
            self._addr = addr
            if self._addr < 0 or self._addr > self.MAX_MAC_ADDR_VALUE:
                raise ValueError('Illegal value for MacAddress')
        elif isinstance(addr, str):
            self._addr = self._parse_address_string(addr)
        else:
            raise ValueError('Illegal parameter-type')

    @classmethod
    def from_octets(cls, binary_mac):
        """Return a legal mac-address from the given binary octet-string"""
        hexstring = octets_to_hexstring(binary_mac)
        return cls(hexstring.rjust(MAC_ADDR_NYBBLES, "0"))

    def toint(self):
        """Returns an integer representation of this MacAddress"""
        return self._addr

    @staticmethod
    def _parse_address_string(addr):
        """Parses the mac-address string and returns an int
        representation of it

        """
        if not isinstance(addr, str):
            raise TypeError('addr argument must be string or unicode')
        addr = _clean_hexstring(addr)
        if len(addr) != MAC_ADDR_NYBBLES:
            raise ValueError('Mac-address must be %s nybbles long' % MAC_ADDR_NYBBLES)

        addr_bytes = [int(addr[x : x + 2], 16) for x in range(0, len(addr), 2)]
        addr = sum(n << shift for n, shift in zip(addr_bytes, _SHIFT_RANGE))
        return addr

    def __str__(self):
        """Return the string representation of this Object.

        >>> ma = MacAddress('e42f3d5')
        >>> str(ma)
        'e4:2f:3d:5'
        >>> ma.__str__()
        'e4:2f:3d:5'
        """
        return _int_to_delimited_hexstring(
            self._addr, self.DEFAULT_DELIM, DELIMS_AND_STEPS[self.DEFAULT_DELIM]
        )

    def __repr__(self):
        """Print the representation of the Object.

        >>> MacAddress('e4:2f:3d:5')
        MacAddress('e4:2f:3d:5')
        """
        return "MacAddress('%s')" % _int_to_delimited_hexstring(
            self._addr, self.DEFAULT_DELIM, DELIMS_AND_STEPS[self.DEFAULT_DELIM]
        )

    def __lt__(self, other):
        return self._compare(other, lambda s, o: s < o)

    def __le__(self, other):
        return self._compare(other, lambda s, o: s <= o)

    def __eq__(self, other):
        return self._compare(other, lambda s, o: s == o)

    def __ne__(self, other):
        return self._compare(other, lambda s, o: s != o)

    def __gt__(self, other):
        return self._compare(other, lambda s, o: s > o)

    def __ge__(self, other):
        return self._compare(other, lambda s, o: s >= o)

    def _compare(self, other, method):
        try:
            other = self.__class__(other)
        except ValueError:
            return NotImplemented
        else:
            return method(self._addr, other._addr)

    def __hash__(self):
        return hash((self.__class__, self._addr))

    def to_string(self, delim=None):
        """Return a mac-address as a string with a given delimiter.
        The delimiter must be one of the legal delimiters '.', '-' or ':'.

        If no delimiter is given the address is returned as a string
        without a delimiter.
        """
        if delim is None:
            return _int_to_delimited_hexstring(self._addr, '', 2)
        if delim not in DELIMS_AND_STEPS:
            raise ValueError('Illegal delimiter')
        return _int_to_delimited_hexstring(self._addr, delim, DELIMS_AND_STEPS[delim])


class MacPrefix(object):
    """Represents the prefix of a range of MacAddress objects.

    Prefixes are allowed on nybble boundaries, but must contain at least 6
    nybbles to be valid. I.e. "00-ab-cd-e" is a valid prefix,
    but "00-ab-c" is not.

    A MacPrefix behaves like a list; len(prefix) will report how many
    addresses are represented by the prefix. The first address is accessible
    as prefix[0] and so on.

    """

    MIN_PREFIX_LEN = 6

    def __init__(self, prefix, min_prefix_len=MIN_PREFIX_LEN):
        prefix = _clean_hexstring(str(prefix))

        self._mask_len = len(prefix)
        if self._mask_len < min_prefix_len:
            raise ValueError(
                "MacPrefix must be at least %s nybbles long" % min_prefix_len
            )
        if self._mask_len > MAC_ADDR_NYBBLES:
            raise ValueError(
                "MacPrefix must be no longer than %s nybbles" % MAC_ADDR_NYBBLES
            )

        self._base = MacAddress(prefix.ljust(MAC_ADDR_NYBBLES, '0'))

    @classmethod
    def from_octets(cls, binary_mac):
        """Creates a MacPrefix from a binary octet string"""
        return cls(octets_to_hexstring(binary_mac))

    def __len__(self):
        """Returns the number of MacAddresses contained in this prefix.

        >>> ma = MacPrefix('e4:23:1d:7e:de:03')
        >>> len(ma)
        1
        >>> ma = MacPrefix('e4:23:1d:7e:de:3')
        >>> len(ma)
        16
        >>> ma = MacPrefix('e4:23:1d:7e:de')
        >>> len(ma)
        256
        """
        unset_nybbles = MAC_ADDR_NYBBLES - self._mask_len
        return 2 ** (unset_nybbles * NUM_BITS_IN_NYBBLE)

    def __getitem__(self, key):
        """Called to implement evaluation of self[key].

        >>> ma = MacPrefix('e4:23:1d')
        >>> for x in ma:
        ...   print(repr(x))
        ...
        MacAddress('e4:23:1d:00:00:00')
        MacAddress('e4:23:1d:00:00:01')
        MacAddress('e4:23:1d:00:00:02')
        MacAddress('e4:23:1d:00:00:03')
                     ...
        MacAddress('e4:23:1d:ff:ff:ff')
        >>> ma[2]
        MacAddress('e4:23:1d:00:00:02')
        >>> ma[11]
        MacAddress('e4:23:1d:00:00:0b')
        >>> ma[-1]
        MacAddress('e4:23:1d:ff:ff:ff')
        """
        if not isinstance(key, int):
            raise TypeError
        if key < 0:
            if abs(key) <= len(self):
                key = len(self) - abs(key)
            else:
                raise IndexError
        else:
            if key >= len(self):
                raise IndexError
        return MacAddress(self._base.toint() + int(key))

    def __str__(self):
        base = str(self._base)
        digitpos = [pos for pos, char in enumerate(base) if char in string.hexdigits]
        digitpos = digitpos[self._mask_len - 1]
        base = base[: digitpos + 1]
        return base.rstrip(''.join(DELIMS_AND_STEPS.keys()))

    def __repr__(self):
        return "MacPrefix(%r)" % str(self)


# Helper functions used by both classes


def _clean_hexstring(hexstr):
    stripped = ''.join(
        i for i in hexstr.strip().replace(" ", "") if i not in DELIMS_AND_STEPS
    )
    if not MAC_ADDRESS_PATTERN.match(stripped):
        raise ValueError("Not a valid hexadecimal string: %s" % hexstr)
    return stripped


def _int_to_delimited_hexstring(mac_addr, delim, step):
    """Formats a long value to a delimited hexadecimal string"""
    mac_addr = '%x' % mac_addr
    mac_addr = mac_addr.rjust(MAC_ADDR_NYBBLES, '0')
    return delim.join(mac_addr[x : x + step] for x in range(0, len(mac_addr), step))


def octets_to_hexstring(octets):
    """Converts an octet string to a printable hexadecimal string"""
    if isinstance(octets, bytes):
        return ''.join("%02x" % byte for byte in octets)
    else:
        return ''.join("%02x" % ord(byte) for byte in octets)
