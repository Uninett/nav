#
# Copyright (C) 2007 Uninett AS
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
"""Implements natural string sorting.

Natural sorting of strings implies that e.g. the string 'foo20bar' will sort
after 'foo3bar' instead of before.

An example of how to naturally sort a directory listing:

  import os, natsort
  foo = os.listdir('/path/to/bar')
  foo.sort(key=natsort.split)
"""
import re

_split_pattern = re.compile(r'(\d+|\D+)')


def split(string):
    """Split a string into digit- and non-digit components."""
    def intcast(n):
        if n.isdigit():
            return int(n)
        else:
            return n

    return [intcast(x) for x in _split_pattern.findall(string)]
