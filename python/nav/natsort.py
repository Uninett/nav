# -*- coding: utf-8 -*-
#
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
"""Implements natural string sorting.

Natural sorting of strings implies that e.g. the string 'foo20bar' will sort
after 'foo3bar' instead of before.

An example of how to naturally sort a directory listing (case insensitive):

  import os, natsort
  foo = os.listdir('/path/to/bar')
  foo.sort(natsort.inatcmp)

Note that this example is highly inefficient, as the inatcmp function has to be
called at least O(n log n) times.  If you are running Python 2.4 or higher, the
more effective way to sort the list foo would be:

  foo.sort(key=natsort.split)

This will pre-generate the list of sorting keys.  If you do not have Python 2.4
or higher, you should use the decorate-sort-undecorate pattern to achieve
maximum efficiency.
"""
import re

_split_pattern = re.compile(r'(\d+|\D+)')

def split(string):
    """Split a string into digit- and non-digit components."""
    def intcast(n):
        if n.isdigit():
            return long(n)
        else:
            return n

    return [intcast(x) for x in _split_pattern.findall(string)]

def natcmp(a, b):
    """Replacement for cmp, performing natural comparison between a
    and b."""
    return cmp(split(a), split(b))

def inatcmp(a, b):
    """Case insensitive version of natcmp."""
    return natcmp(a.lower(), b.lower())

def decorated_sort(l):
    """
    Sort the list of strings l naturally, using the decorate-sort-undecorate
    pattern.  NB: Does not sort l in-place, but returns a new list with the
    elements of l sorted naturally.

    If using Python 2.4 or newer, use l.sort(key=natsort.split) instead.
    """
    deco = [ (split(element), i, element) for i, element in enumerate(l) ]
    deco.sort()
    new_list = [ element for _, _, element in deco ]
    return new_list


