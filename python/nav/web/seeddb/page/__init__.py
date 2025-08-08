# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django.shortcuts import render

from nav.web.seeddb.constants import TITLE_DEFAULT


def index(request):
    """Index page. Nothing particularly interesting going on."""
    return render(
        request,
        'seeddb/index.html',
        {
            'title': TITLE_DEFAULT,
            'navpath': [('Home', '/'), ('Seed DB', None)],
            'active': {'index': True},
        },
    )


def not_implemented(*_args, **_kwargs):
    """Simple method used with the view_switcher.

    Raises "not implemented if called, but the list pages should make sure this
    function is never called.
    """
    raise NotImplementedError()


def view_switcher(
    request,
    list_view=None,
    move_view=None,
    delete_view=None,
    download_qr_codes_view=None,
):
    """Selects appropriate view depending on POST data."""
    if request.method == 'POST':
        if 'move' in request.POST:
            return move_view(request)
        elif 'delete' in request.POST:
            return delete_view(request)
        elif 'qr_code' in request.POST:
            return download_qr_codes_view(request)
    return list_view(request)
