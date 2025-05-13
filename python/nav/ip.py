#
# Copyright (C) 2017, 2019 Uninett AS
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
"""
This module exists only to work around deficiencies in IPy, but could
potentially evolve to become a facade for other modules in the event of a
transition away from the IPy library.
"""

import IPy


class IP(IPy.IP):
    """Class for handling IP addresses and networks."""

    # Stupid IPy.IP will refuse to be compared with other types,
    # which makes sorting of various dictionaries for pretty printing
    # and such nigh-on impossible. Here we make some workarounds for this.

    def __cmp__(self, other):
        """Overrides IPy.IP's __cmp__, which us used by all its rich comparison
        operators, even though Python no longer consults __cmp__ directly.
        """
        try:
            return super(IP, self).__cmp__(other)
        except TypeError:
            return (self.ip > other) - (self.ip < other)

    def __eq__(self, other):
        try:
            return super(IP, self).__eq__(other)
        except TypeError:
            return False

    def __hash__(self):
        return super(IP, self).__hash__()
