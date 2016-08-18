#
# Copyright (C) 2016 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Controller functions for prefix details page"""

from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404

from nav.web import utils
from nav.models.manage import Prefix


def index(request):
    """Index controller, does not do anything atm"""
    return render(request, 'info/prefix/base.html', get_context())


def prefix_details(request, prefix_id):
    """Controller for rendering prefix details"""
    prefix = get_object_or_404(Prefix, pk=prefix_id)
    return render(request, 'info/prefix/details.html', get_context(prefix))


def get_context(prefix=None):
    """Returns a object suitable for a breadcrumb"""
    navpath = [('Home', '/'), ('Prefix Details', reverse('prefix-index'))]
    if prefix:
        navpath.append((prefix.net_address,))
    return {
        'prefix': prefix,
        'navpath': navpath,
        'title': utils.create_title(navpath)
    }
