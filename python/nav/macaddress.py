#
# Copyright 2013 (C) UNINETT AS
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

# A range of left shift values for the 6 bytes in a MAC address
_SHIFT_RANGE = tuple(x*8 for x in reversed(range(6)))


class MacAddress(object):
    """A representation of either a single MAC address or a MAC address
    prefix, loosely modeled on IPy.IP for IP addresses.

    """
    # Default delimiter for a mac-address as a string.
    DEFAULT_DELIM = ':'
    # Legal delimiters and the number of nybbles between them.
    DELIMS_AND_STEPS = {'.': 4, ':': 2, '-': 2, }
    # Maximum number of nybbles in a mac-address.
    MAX_MAC_ADDR_LEN = 12
    # Minimum number of nybbles in a mac-address.
    MIN_MAC_ADDR_LEN = 6
    # Maximum number of bits in an mac-address.
    NUM_BITS_MAC_ADDR = 48
    # Maximum value for a mac-address when all bits are set.
    MAX_MAC_ADDR_VALUE = 0xffffffffffff
    # Obviously number of bits for a nybble.
    NUM_BITS_IN_NYBBLE = 4
    # Strip for delimiters and test against this pattern.
    MAC_ADDRESS_PATTERN = re.compile('^[a-fA-F0-9]{6,12}$')
    # To hold the value for a mac-address as an int.
    _addr = None
    # The number of nybbles in this address.
    _prefix_len = -1
    # The maximum number of possible addresses that are able to
    # represent full and legal mac-addresses.
    _addr_len = -1

    def __init__(self, addr):
        # pylint: disable=W0212
        if isinstance(addr, MacAddress):
            self._addr = addr._addr
            self._prefix_len = addr._prefix_len
            self._addr_len = addr._addr_len
        else:
            if isinstance(addr, (int, long)):
                self._addr = long(addr)
                if self._addr < 0 or self._addr > self.MAX_MAC_ADDR_VALUE:
                    raise ValueError('Illegal value for address')
                self._prefix_len = self.MAX_MAC_ADDR_LEN
            elif isinstance(addr, (str, unicode)):
                (self._addr, self._prefix_len) = self._parse_address(addr)
            else:
                raise ValueError('Illegal parameter-type')
            self._addr_len = 2 ** (self.NUM_BITS_MAC_ADDR -
                                   (self._prefix_len *
                                    self.NUM_BITS_IN_NYBBLE))

    @classmethod
    def from_octets(cls, binary_mac):
        """Return a legal mac-address from the given binary octet-string"""
        max_length = 6
        if binary_mac:
            binary_mac = binary_mac[-6:].rjust(max_length, '\x00')
            return cls(":".join("%02x" % ord(x) for x in binary_mac))

    def _parse_address(self, addr):
        """Parse the mac-address string and return a tuple of the long-value
        for the address and the length of the address-string (number of nybbles
        in the given address).
        """
        if not isinstance(addr, (str, unicode)):
            raise TypeError('addr argument must be string or unicode')
        addr = ''.join(i for i in addr.strip()
                       if i not in self.DELIMS_AND_STEPS)
        orig_len = len(addr)
        if orig_len < self.MIN_MAC_ADDR_LEN:
            raise ValueError('Mac-address too short; Minimum %d nybbles' %
                             self.MIN_MAC_ADDR_LEN)
        if orig_len > self.MAX_MAC_ADDR_LEN:
            raise ValueError('Mac-address too long; Maximum %d nybbles' %
                             self.MAX_MAC_ADDR_LEN)
        if not self.MAC_ADDRESS_PATTERN.match(addr):
            raise ValueError("Mac-address contain illegal values")

        addr = addr.ljust(self.MAX_MAC_ADDR_LEN, '0')
        addr_bytes = [long(addr[x:x + 2], 16) for x in range(0, len(addr), 2)]
        addr = sum(n << shift for n, shift in zip(addr_bytes, _SHIFT_RANGE))
        return addr, orig_len

    @classmethod
    def _add_delimiter(cls, mac_addr, prefix_len, delim, step):
        """Format the mac-address to a string with delimiters"""
        mac_addr = ('%x' % mac_addr)
        mac_addr = mac_addr.rjust(cls.MAX_MAC_ADDR_LEN, '0')
        if ((prefix_len >= cls.MIN_MAC_ADDR_LEN) and
           (prefix_len < cls.MAX_MAC_ADDR_LEN)):
            mac_addr = mac_addr[0:prefix_len]
        return delim.join(mac_addr[x:x + step]
                          for x in range(0, len(mac_addr), step))

    def __str__(self):
        """Return the string representation of this Object.

        >>> ma = MacAddress('e42f3d5')
        >>> str(ma)
        'e4:2f:3d:5'
        >>> ma.__str__()
        'e4:2f:3d:5'
        """
        return self.__unicode__()

    def __unicode__(self):
        """Return the unicode representation of this Object.

        >>> ma = MacAddress('e42f3d5')
        >>> unicode(ma)
        u'e4:2f:3d:5'
        >>> ma.__unicode__()
        u'e4:2f:3d:5'
        """
        return self._add_delimiter(self._addr, self._prefix_len,
                                   self.DEFAULT_DELIM,
                                   self.DELIMS_AND_STEPS[self.DEFAULT_DELIM])

    def __repr__(self):
        """Print the representation of the Object.

        >>> MacAddress('e4:2f:3d:5')
        MacAddress('e4:2f:3d:5')
        """
        return ("MacAddress('%s')" %
                self._add_delimiter(self._addr,
                                    self._prefix_len,
                                    self.DEFAULT_DELIM,
                                    self.DELIMS_AND_STEPS[self.DEFAULT_DELIM]))

    def __len__(self):
        """Return the maximum number of possible addresses
        that are able to represent full and legal mac-addresses.

        >>> ma = MacAddress('e4:23:1d:7e:de:03')
        >>> len(ma)
        1
        >>> ma = MacAddress('e4:23:1d:7e:de:3')
        >>> len(ma)
        16
        >>> ma = MacAddress('e4:23:1d:7e:de')
        >>> len(ma)
        256
        """
        return self._addr_len

    def __getitem__(self, key):
        """Called to implement evaluation of self[key].

        >>> ma = MacAddress('e4:23:1d')
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
        if not isinstance(key, (int, long)):
            raise TypeError
        if key < 0:
            if abs(key) <= self._addr_len:
                key = self._addr_len - abs(key)
            else:
                raise IndexError
        else:
            if key >= self._addr_len:
                raise IndexError
        return MacAddress(self._add_delimiter((self._addr + long(key)),
                          self.MAX_MAC_ADDR_LEN,
                          self.DEFAULT_DELIM,
                          self.DELIMS_AND_STEPS[self.DEFAULT_DELIM]))

    def __cmp__(self, other):
        """Called by comparison operations.

        Should return a negative integer if self < other, zero if self
        == other, a positive integer if self > other.
        If other is not an object that can get converted to a mac-address
        this method will always return less than zero.
        """
        mac_addr = other
        if isinstance(other, (str, unicode, int, long)):
            try:
                mac_addr = MacAddress(other)
            except ValueError:
                mac_addr = None
        # pylint: disable=W0212
        if isinstance(mac_addr, MacAddress):
            if self._addr < mac_addr._addr:
                return -1
            elif self._addr > mac_addr._addr:
                return 1
            else:
                return 0
        return -1

    def __lt__(self, other):
        """Return True of this object is less than other"""
        return self.__cmp__(other) < 0

    def __le__(self, other):
        """Return True of this object is less than or equal other"""
        return self.__cmp__(other) <= 0

    def __eq__(self, other):
        """Return True of this object is equal other"""
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        """Return True of this object is not equal other"""
        return self.__cmp__(other) != 0

    def __gt__(self, other):
        """Return True of this object is greater than other"""
        return self.__cmp__(other) > 0

    def __ge__(self, other):
        """Return True of this object is greater than or equal other"""
        if isinstance(other, MacAddress):
            return self.__cmp__(other) >= 0

    def __hash__(self):
        """Return this object's hash-value"""
        return hash((self._addr, self._prefix_len))

    def to_string(self, delim=None):
        """Return a mac-address as a string with a given delimiter.
        The delimiter must be one of the legal delimiters '.', '-' or ':'.

        If no delimiter is given the address is returned as a string
        without a delimiter.
        """
        if delim is None:
            return self._add_delimiter(self._addr, self._prefix_len, '', 2)
        if not delim in self.DELIMS_AND_STEPS:
            raise ValueError('Illegal delimiter')
        return self._add_delimiter(self._addr, self._prefix_len, delim,
                                   self.DELIMS_AND_STEPS[delim])
