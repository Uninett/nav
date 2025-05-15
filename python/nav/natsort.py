#
# Copyright (C) 2007, 2019 Uninett AS
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
from functools import total_ordering

_split_pattern = re.compile(r'(\d+|\D+)')


def split(string):
    """Split a string into digit- and non-digit components."""
    return [ComparableThing(x) for x in _split_pattern.findall(string)]


@total_ordering
class ComparableThing(object):
    """Wrapper class for comparing both strings and integers.

    This exists to impose a stable sort order for strings split by natsort.split, even
    on Python 3, which doesn't want to compare objects of different types.

    """

    def __init__(self, value):
        if isinstance(value, str) and value.isdigit():
            self.value = int(value)
        else:
            self.value = value

    def __eq__(self, other):
        if isinstance(other, ComparableThing):
            return self.value == other.value
        return self.value == other

    def __lt__(self, other):
        if not isinstance(other, ComparableThing):
            return self.value < other

        if isinstance(self.value, int) and not isinstance(other.value, int):
            return True
        if isinstance(self.value, str) and not isinstance(other.value, str):
            return False

        return self.value < other.value

    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)
