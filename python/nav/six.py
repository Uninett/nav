#
# Copyright (C) 2019 Uninett AS
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
Various functions that we need to keep code in python2 and python3 looking the
same that six lacks.

"""
from __future__ import absolute_import

from django.utils import six

if six.PY3:

    def encode_array(array):
        return array.tobytes()


else:

    def encode_array(array):
        return array.tostring()


__all__ = [
    'encode_array',
]
