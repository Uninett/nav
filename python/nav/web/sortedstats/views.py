#
# Copyright (C) 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV)
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
"""Sorted statistics views."""

import logging
from django.shortcuts import render

from .forms import ViewForm
from . import CLASSMAP

_logger = logging.getLogger(__name__)


def index(request):
    """Sorted stats search & result view"""
    result = None
    if 'view' in request.GET:
        form = ViewForm(request.GET)
        if form.is_valid():
            cls = CLASSMAP[form.cleaned_data['view']]
            result = cls(form.cleaned_data['timeframe'], form.cleaned_data['rows'])
            result.collect()

    else:
        form = ViewForm()

    context = {
        'title': 'Statistics',
        'navpath': [('Home', '/'), ('Statistics', False)],
        'result': result,
        'form': form,
    }

    return render(request, 'sortedstats/sortedstats.html', context)
