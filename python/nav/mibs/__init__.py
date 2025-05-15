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
"""MIB parsing and MIB-aware data retrieval."""

from . import mibretriever

modules = mibretriever.MibRetrieverMaker.modules


def reduce_index(result):
    """Reduce a MIB table result dictionary's keys.

    Given that the keys (table indexes) of the result dictionary are
    single-element tuples, this function will replace the tuples with
    the single element in them.

    A convenient translator to add to the callback chain of many table
    retrievals.  Notes: This will alter the original result dictionary
    instance.

    """
    for key, value in list(result.items()):
        if len(key) == 1:
            del result[key]
            key = key[0]
            result[key] = value
    return result
