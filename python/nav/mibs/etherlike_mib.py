# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Uninett AS
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
# more details. You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Implements a EtherLike-MIB MibRetriever and associated functionality."""

from twisted.internet import defer
from nav.smidumps import get_mib
from . import mibretriever


class EtherLikeMib(mibretriever.MibRetriever):
    """MibRetriever for EtherLike-MIB"""

    mib = get_mib('EtherLike-MIB')

    @defer.inlineCallbacks
    def get_duplex(self):
        """Get a mapping of ifindexes->duplex status."""
        data = yield self.retrieve_columns(('dot3StatsDuplexStatus',))
        duplex = self.translate_result(data)

        result = {
            index[0]: row['dot3StatsDuplexStatus'] for index, row in duplex.items()
        }
        return result
