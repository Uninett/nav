# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Norwegian University of Science and Technology
# Copyright (C) 2007 UNINETT AS
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
"""General utility functions for Network Administration Visualized"""

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

def round_robin(collection):
    '''Returns a generator that will loop over the collection forever in a
       round robin fashion'''
    index = 0

    while True:
        yield collection[index]
        index = (index + 1) % len(collection)
