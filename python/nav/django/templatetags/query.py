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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Template tags related to manipulation of URLs with query parameters"""

from django import template

from nav.django.utils import reverse_with_query

register = template.Library()


@register.simple_tag
def query(viewname, **kwargs):
    """Gets a URL to a named view and adorns it with query arguments"""
    return reverse_with_query(viewname, **kwargs)
