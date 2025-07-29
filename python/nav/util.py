#
# Copyright (C) 2007, 2011-2013 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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
import re
import stat
import socket
import datetime
from functools import wraps
from importlib.resources import as_file, files as resource_files
from itertools import chain, tee, groupby, islice
from operator import itemgetter
from secrets import token_hex

import IPy


def gradient(start, stop, steps):
    """Create and return a sequence of steps representing an integer
    gradient from the start value to the stop value.

    The more steps, the smoother the gradient."""
    distance = stop - start
    # Reduce by 1 step to include both endpoints, but never reduce it
    # to zero (we always want at least to values)
    steps = steps - 1 if steps > 1 else 1
    increment = distance / float(steps)
    grad = []
    for i in range(steps):
        grad.append(int(round(start + i * increment)))
    grad.append(stop)
    return grad


def color_gradient(start, stop, steps):
    """Does the same as the gradient function, but the start and
    stop values are RGB triplets (3-element tuples)"""
    red = gradient(start[0], stop[0], steps)
    green = gradient(start[1], stop[1], steps)
    blue = gradient(start[2], stop[2], steps)

    grad = zip(red, green, blue)
    return list(grad)


def colortohex(triplet):
    """Returns a hexadecimal string representation of a 3-tuple RGB
    color triplet.

    Useful for converting internal color triplets to web
    representation."""
    return ('%02x' * 3) % triplet


def is_valid_ip(ip, strict=False):
    """Verifies that a string is a single, valid IPv4 or IPv6 address.

    :param ip: The string to test for validity
    :param strict: If False, the quite lax rules of IPy.IP will be used to validate the
                   IP address - partial IP addresses and even integers will parsed.
                   If True, the stricter rules of the system socket library are used.
    """
    if strict:
        return _is_valid_ip_socket(ip)
    else:
        return _is_valid_ip_ipy(ip)


def _is_valid_ip_socket(ip):
    """Checks for ip validity using the socket library"""
    try:
        socket.inet_pton(socket.AF_INET, ip)  # IPv4
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, ip)  # IPv6
        except socket.error:
            return False
        else:
            return True
    except UnicodeError:
        # Definitely not an IP address!
        return False
    else:
        return True


def _is_valid_ip_ipy(ip):
    """Checks for ip validity using the IPy library

    A cleaned up version of the IP address string is returned if it is verified,
    otherwise a false value is returned.
    """
    if isinstance(ip, str) and not ip.isdigit():
        try:
            valid_ip = IPy.IP(ip)
            if valid_ip.len() == 1:
                return str(valid_ip)
        except ValueError:
            pass
    return False


def is_valid_cidr(cidr):
    """Verifies that a string is valid IPv4 or IPv6 CIDR specification.

    A cleaned up version of the CIDR string is returned if it is verified,
    otherwise a false value is returned.

    Uses the IPy library to verify addresses.
    """
    if isinstance(cidr, str) and not cidr.isdigit() and '/' in cidr:
        try:
            valid_cidr = IPy.IP(cidr) is not None
        except (ValueError, TypeError):
            return False
        else:
            return valid_cidr
    return False


def is_valid_mac(mac):
    """Verify that this mac-address is valid"""
    if re.match("[0-9a-f]{2}([-:][0-9a-f]{2}){5}$", mac.lower()):
        return True
    return False


def which(cmd, search_path=None):
    """Returns the full path of cmd if found in a list of search paths and it
    is executable.

    :param cmd: Name of an executable file.
    :param search_path: List of search paths. If omitted, the OS environment
                        variable PATH is used.
    :returns: A full path to cmd, or None if not found or not executable.

    """
    if search_path is None:
        search_path = os.environ['PATH'].split(':')
    paths = (os.path.join(path, cmd) for path in search_path)

    for path in paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path


def is_setuid_root(path):
    """Return True if the file is owned by root and has
    the setuid bit set."""

    # Can't be setuid root if it's not there.
    if not os.path.isfile(path):
        return False

    pstat = os.stat(path)

    # Owned by root?
    if pstat.st_uid != 0:
        return False

    # Setuid bit set?
    if pstat.st_mode & stat.S_ISUID == 0:
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
    return dict((k, [d.get(k, None) for d in dicts]) for k in keys)


def splitby(predicate, iterable):
    """Splits an iterable in two iterables, based on a predicate.

    :returns: A tuple of two iterables: (true_iter, false_iter)

    """
    predicated = ((v, predicate(v)) for v in iterable)
    iter1, iter2 = tee(predicated)
    return (v for (v, p) in iter1 if p), (v for (v, p) in iter2 if not p)


def first_true(iterable, default=None, pred=None):
    """Returns the first element of iterable that evaluates to True.

    :param default: Default return value if none of the elements of iterable
                    were true.
    :param pred: Optional predicate function to evaluate the truthfulness of
                 elements.
    """
    return next(filter(pred, iterable), default)


def chunks(iterable, size):
    """Yields successive chunks from iterable. Each chunk will be at most `size`
    elements long. For example,

    >>> list(chunks(range(9), 4))
    [(0, 1, 2, 3), (4, 5, 6, 7), (8,)]
    """
    iterator = iter(iterable)
    return iter(lambda: tuple(islice(iterator, size)), ())


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
        return "%s(%r, %r)" % (self.__class__.__name__, self._min, self._max)

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
        for offset in range(0, count):
            yield IPy.IP(self._min.int() + offset)

    def __getitem__(self, index):
        if index >= self.len() or index < -self.len():
            raise IndexError('index out of range')
        if index >= 0:
            return IPy.IP(self._min.int() + index)
        else:
            return IPy.IP(self._max.int() + index + 1)

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
            return addr, addr

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

        return from_ip, to_ip

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
        return ip1, ip2

    @classmethod
    def _parse_as_network(cls, rangestring):
        try:
            network, mask = rangestring.split('/')
        except ValueError:
            raise ValueError("multiple network masks found")
        if not mask:
            mask = cls.get_mask_for_network(network)

        iprange = IPy.IP(network).make_net(mask)
        return iprange[0], iprange[-1]

    @classmethod
    def get_mask_for_network(cls, network):
        """Returns a suitable mask for the given network address.

        Defaults to a 24 bit mask. Override this to do other magic, like look
        up a matching prefix from the NAV database.

        """
        return '24'


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


def parse_interval(string):
    """Parses a string for simple time interval definitions and returns a
    number of seconds represented.

    Examples::
    >>> parse_interval('1s')
    1
    >>> parse_interval('1m')
    60
    >>> parse_interval('1h')
    3600
    >>> parse_interval('1d')
    86400
    >>>


    :param string: A string specifying an interval
    :return: A number of seconds as an int

    """
    string = string.strip()

    if string == '':
        return 0

    if string.isdigit():
        return int(string)

    string, unit = int(string[:-1]), string[-1:].lower()

    if unit == 'd':
        return string * 60 * 60 * 24
    elif unit == 'h':
        return string * 60 * 60
    elif unit == 'm':
        return string * 60
    elif unit == 's':
        return string

    raise ValueError('Invalid time format: %s%s' % (string, unit))


def address_to_string(ip, port):
    """Converts an IP address and port pair into a printable string.

    An IPv6 address will be encapsulated in square brackets to separate it
    from the port number.

    """
    ip = IPy.IP(ip)
    ip = str(ip) if ip.version() == 4 else "[%s]" % ip
    return "%s:%s" % (ip, port)


def auth_token():
    """Generates a hex token that can be used as an OAuth API token"""
    return token_hex(32)


def consecutive(seq):
    """Yields a series of ranges found in the number sequence.

    :param seq: A sequence of numbers.
    """
    data = ((y - x, y) for x, y in enumerate(sorted(seq)))
    for _key, group in groupby(data, itemgetter(0)):
        group = [item[1] for item in group]
        yield group[0], group[-1]


class NumberRange(object):
    """
    Represents a sequence of numbers that can be compacted to a series of
    number ranges.
    """

    def __init__(self, sequence):
        self.ranges = list(consecutive(sequence))

    def __iter__(self):
        return iter(self._range_to_str(x, y) for x, y in self.ranges)

    def __str__(self):
        return ", ".join(self)

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, self)

    @staticmethod
    def _range_to_str(x, y):
        if x == y:
            return str(x)
        else:
            return "{}-{}".format(x, y)


def resource_filename(package, filename):
    """Return the path of the filename as it is inside the package

    package: either a dotted path to a module or a module object
    filename: str or pathlib.Path
    """
    ref = resource_files(package) / filename
    with as_file(ref) as path:
        return str(path)


def resource_bytes(package, filename):
    """Read and return a bytes-object of the filename found in the package

    package: either a dotted path to a module or a module object
    filename: str or pathlib.Path
    """
    ref = resource_files(package) / filename
    return ref.read_bytes()
