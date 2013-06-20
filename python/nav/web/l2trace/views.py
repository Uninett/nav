#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
# Copyright (C) 2007, 2010, 2011, 2013 UNINETT AS
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
"""Layer 2 trace views"""

from django.shortcuts import render_to_response
from django.template import RequestContext

from . import L2TraceQuery
from .forms import L2TraceForm


def index(request):
    """Single view function of l2trace."""

    query = {
        'host_from': request.GET.get('host_from'),
        'host_to': request.GET.get('host_to'),
    }
    form = L2TraceForm(query)

    context = {
        'title': 'Layer 2 Traceroute',
        'navpath': [('Home', '/'), ('Layer 2 Traceroute', '/l2trace')],
        'form': form
    }

    if form.is_valid():
        host_from = form.cleaned_data.get('host_from')
        host_to = form.cleaned_data.get('host_to')
        l2tracer = L2TraceQuery(host_from, host_to)
        l2tracer.trace()
        context.update({'l2tracer': l2tracer})

    return render_to_response('l2trace/l2trace.html', context,
                              RequestContext(request))
