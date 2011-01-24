#
# Copyright 2003, 2004 (C) Norwegian University of Science and Technology
# Copyright 2007, 2010, 2011 (C) UNINETT AS
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

from . import L2TraceForm, L2TraceQuery
from django.http import HttpResponse

from nav.web.templates.l2traceTemplate import l2traceTemplate

def index(req):
    """Single view function of l2trace."""
    page = l2traceTemplate()
    page.l2tracer = None
    page.form = L2TraceForm(req.GET.get("host_from", None),
                            req.GET.get("host_to", None))

    if "host_from" in req.GET or "host_to" in req.GET:
        page.l2tracer = L2TraceQuery(req.GET.get("host_from", None),
                                     req.GET.get("host_to", None))
        page.l2tracer.trace()

    return HttpResponse(page.respond())
