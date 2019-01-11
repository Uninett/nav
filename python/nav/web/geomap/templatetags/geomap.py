#
# Copyright (C) 2018 UNINETT
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
from nav.web.geomap.utils import is_nan

from django import template

register = template.Library()


@register.filter(name='nan2none')
def filter_nan2none(value):
    """Convert the NaN value to None, leaving everything else unchanged.

    This function is meant to be used as a Django template filter. It
    is useful in combination with filters that handle None (or any
    false value) specially, such as the 'default' filter, when one
    wants special treatment for the NaN value. It is also useful
    before the 'format' filter to avoid the NaN value being formatted.

    """
    if is_nan(value):
        return None
    return value


@register.filter(name='format')
def filter_format(value, arg):
    """Format value according to format string arg.

    This function is meant to be used as a Django template filter.

    """
    try:
        return arg % value
    except TypeError:
        return ''
