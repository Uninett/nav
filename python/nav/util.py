#
# Copyright (C) 2005 Norwegian University of Science and Technology
# Copyright (C) 2007, 2011 UNINETT AS
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
"""General utility functions for Network Administration Visualized"""

import os
import stat
import datetime
from functools import wraps
from itertools import chain, tee

import IPy

def gradient(start, stop, steps):
    """Create and return a sequence of steps representing an integer
    gradient from the start value to the stop value.

    The more steps, the smoother the gradient."""
    distance = (stop - start)
    # Reduce by 1 step to include both endpoints, but never reduce it
    # to zero (we always want at least to values)
    steps = steps > 1 and steps-1 or 1
    increment = distance / float(steps)
    grad = []
    for i in xrange(steps):
        grad.append(int(round(start + i*increment)))
    grad.append(stop)
    return grad

def color_gradient(start, stop, steps):
    """Does the same as the gradient function, but the start and
    stop values are RGB triplets (3-element tuples)"""
    r = gradient(start[0], stop[0], steps)
    g = gradient(start[1], stop[1], steps)
    b = gradient(start[2], stop[2], steps)

    grad = zip(r, g, b)
    return grad

def colortohex(triplet):
    """Returns a hexadecimal string representation of a 3-tuple RGB
    color triplet.

    Useful for converting internal color triplets to web
    representation."""
    return ('%02x'*3) % triplet

def isValidIP(ip):
    """Verifies that a string is a single, valid IPv4 or IPv6 address.

    A cleaned up version of the IP address string is returned if it is
    verified, otherwise a false value is returned.

    Uses the IPy library to verify addresses.
    """
    if isinstance(ip, (str, unicode)) and not ip.isdigit():
        try:
            validIP = IPy.IP(ip)
            if len(validIP) == 1:
                return str(validIP)
        except ValueError:
            pass
    return False

# copy to more PEP8-friendly name
# FIXME: update callers and rename original
is_valid_ip = isValidIP

def is_valid_cidr(cidr):
    """Verifies that a string is valid IPv4 or IPv6 CIDR specification.

    A cleaned up version of the CIDR string is returned if it is verified,
    otherwise a false value is returned.

    Uses the IPy library to verify addresses.
    """
    if isinstance(cidr, basestring) and not cidr.isdigit() and '/' in cidr:
        try:
            valid_cidr = IPy.IP(cidr)
        except (ValueError, TypeError):
            return False
        else:
            return valid_cidr
    return False

def which(cmd):
    """Return full path to cmd (if found in $PATH and is executable),
    or None."""
    pathstr = os.environ['PATH']
    dirs = pathstr.split(':')

    for d in dirs:
        path = os.path.join(d, cmd)

        if not os.path.isfile(path):
            continue

        if not os.access(path, os.X_OK):
            continue
        
        return path

    return None

def is_setuid_root(path):
    """Return True if the file is owned by root and has
    the setuid bit set."""

    # Can't be setuid root if it's not there.
    if not os.path.isfile(path):
        return False

    s = os.stat(path)

    # Owned by root?
    if s.st_uid != 0:
        return False

    # Setuid bit set?
    if s.st_mode & stat.S_ISUID == 0:
        return False

    # Yay, passed all test!
    return True


def mergedicts(*dicts):
    """Merges a sequence of dictionaries in order.

    Example usage:

    >>> d1 = {1: 10, 2: 20}
    >>> d2 = {1: 100, 2: 200, 3: 300}
    >>> mergedicts(d1, d2)
    {1: [10, 100], 2: [20, 200], 3: [None, 300]}

    """
    keys = chain(*dicts)
    return dict((k, [d.get(k, None) for d in dicts])
                for k in keys)

def splitby(predicate, iterable):
    """Splits an iterable in two iterables, based on a predicate.

    :returns: A tuple of two iterables: (true_iter, false_iter)

    """
    predicated = ((v, predicate(v)) for v in iterable)
    iter1, iter2 = tee(predicated)
    return (v for (v, p) in iter1 if p), (v for (v, p) in iter2 if not p)

class IPRange(object):
    """An IP range representation.

    An IPRange object is both iterable and indexable. All addresses are
    calculated on the fly based on the range endpoints, ensuring memory
    efficiency.

    Use the from_string() factory method to create a range object from a
    string representation.

    """

    def __init__(self, start, stop):
        """Creates an IP range representation including both the start and
        stop endpoints.

        """
        start = IPy.IP(start)
        stop = IPy.IP(stop)
        self._min = min(start, stop)
        self._max = max(start, stop)

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__,
                               self._min, self._max)

    def __contains__(self, item):
        return item >= self._min and item <= self._max

    def __len__(self):
        return self._max.int() - self._min.int() + 1

    def len(self):
        """Returns the length of the range.

        When working with IPv6, this may actually be preferable to
        len(iprange), as huge prefixes may cause an OverflowError when using
        the standard Python len() protocol.

        """
        return self.__len__()

    def __iter__(self):
        count = self.len()
        for offset in xrange(0, count):
            yield IPy.IP(self._min.int()+offset)

    def __getitem__(self, index):
        if index >= self.len() or index < -self.len():
            raise IndexError('index out of range')
        if index >= 0:
            return IPy.IP(self._min.int()+index)
        else:
            return IPy.IP(self._max.int()+index+1)

    @classmethod
    def from_string(cls, rangestring):
        """Creates an IP range representation from a string.

        Examples:

        >>> IPRange.from_string('10.0.1.20-10.0.1.30')
        IPRange(IP('10.0.1.20'), IP('10.0.1.30'))
        >>> IPRange.from_string('10.0.1.0/24')
        IPRange(IP('10.0.1.0'), IP('10.0.1.255'))
        >>> IPRange.from_string('fe80:700::aaa-fff')
        IPRange(IP('fe80:700::aaa'), IP('fe80:700::fff'))

        """

        start, stop = cls._parse(rangestring.strip())
        return cls(start, stop)

    @classmethod
    def _parse(cls, rangestring):
        if '-' in rangestring:
            return cls._parse_as_range(rangestring)
        elif '/' in rangestring:
            return cls._parse_as_network(rangestring)
        else:
            addr = IPy.IP(rangestring)
            return (addr, addr)

    @classmethod
    def _parse_as_range(cls, rangestring):
        try:
            from_ip, to_ip = rangestring.split('-')
        except ValueError:
            raise ValueError("multiple ranges found")

        try:
            from_ip, to_ip = cls._assemble_range(from_ip, to_ip)
        except ValueError:
            from_ip = IPy.IP(from_ip)
            to_ip = IPy.IP(to_ip)

        return (from_ip, to_ip)

    @staticmethod
    def _assemble_range(from_ip, to_ip):
        """Parses 10.0.42.0-62 as 10.0.42.0-10.0.42.62, raising a ValueError
        if not possible.

        """
        ip1 = IPy.IP(from_ip)
        sep = ":" if ip1.version() == 6 else "."
        prefix, _suffix = from_ip.rsplit(sep, 1)
        assembled = sep.join([prefix, to_ip])
        ip2 = IPy.IP(assembled)
        return (ip1, ip2)

    @classmethod
    def _parse_as_network(cls, rangestring):
        try:
            network, mask = rangestring.split('/')
        except ValueError:
            raise ValueError("multiple network masks found")
        if not mask:
            mask = cls.get_mask_for_network(network)

        iprange = IPy.IP(network).make_net(mask)
        return (iprange[0], iprange[-1])

    # pylint: disable=W0613
    @classmethod
    def get_mask_for_network(cls, network):
        """Returns a suitable mask for the given network address.

        Defaults to a 24 bit mask. Override this to do other magic, like look
        up a matching prefix from the NAV database.

        """
        return '24'

# pylint: disable=C0103,R0903
class cachedfor(object):
    """Decorates a function with no arguments to cache its result for a period
    of time.

    """
    def __init__(self, max_age):
        self.max_age = max_age
        self.value = None
        self.func = None
        self.updated = datetime.datetime.min

    def __call__(self, func):
        self.func = func
        @wraps(func)
        def _wrapper():
            age = datetime.datetime.now() - self.updated
            if age >= self.max_age:
                self.value = self.func()
                self.updated = datetime.datetime.now()
            return self.value

        return _wrapper

def synchronized(lock):
    """Synchronization decorator.

    Decorates a function to ensure it can only run in a single thread at a
    time.

    :param lock: A threading.Lock object.

    """
    def _decorator(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            lock.acquire()
            try:
                return func(*args, **kwargs)
            finally:
                lock.release()
        return _wrapper
    return _decorator

