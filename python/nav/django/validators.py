#
# Copyright (C) 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from decimal import Decimal, InvalidOperation

def is_valid_point_string(point_string):
    if point_string.startswith('(') and point_string.endswith(')'):
        if len(point_string.split(',')) == 2:
            x_point, y_point = point_string[1:-1].split(',')
            try:
                Decimal(x_point.strip())
                Decimal(y_point.strip())
            except InvalidOperation:
                pass
            else:
                return True
    return False
