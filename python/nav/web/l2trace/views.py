#
# Copyright (C) 2007, 2010, 2011, 2013, 2014 Uninett AS
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
"""Layer 2 trace views"""

from django.shortcuts import render

from .forms import L2TraceForm


def index(request):
    """Single view function of l2trace."""

    if 'host_from' in request.GET:
        form = L2TraceForm(request.GET)
    else:
        form = L2TraceForm()

    context = {
        'title': 'Layer 2 Traceroute',
        'navpath': [('Home', '/'), ('Layer 2 Traceroute', '/l2trace')],
        'form': form,
    }

    if form.is_valid():
        context.update({'l2tracer': form.l2tracer})

    return render(request, 'l2trace/l2trace.html', context)
