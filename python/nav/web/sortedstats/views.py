#
# Copyright (C) 2006 Norwegian University of Science and Technology
# Copyright (C) 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
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
"""Sorted statistics views."""

import logging
from operator import itemgetter

from django.shortcuts import render_to_response
from django.template import RequestContext

from .statmodules import (StatCpuAverage, StatUptime, StatIfInOctets,
                          StatIfOutOctets, StatIfOutErrors, StatIfInErrors)

_logger = logging.getLogger(__name__)

TIMEFRAMES = (
    ('-1h', 'Last Hour'),
    ('-1d', 'Last Day'),
    ('-1w', 'Last Week'),
    ('-1month', 'Last Month'),
)

CLASSMAP = {'cpu_routers_highestmax': StatCpuAverage,
            'uptime': StatUptime,
            'ifinoctets': StatIfInOctets,
            'ifoutoctets': StatIfOutOctets,
            'ifouterrors': StatIfOutErrors,
            'ifinerrors': StatIfInErrors,
            }


def index(request):
    """Sorted stats search & result view"""
    numrows = int(request.GET.get('numrows', 5))
    fromtime = request.GET.get('fromtime', '-1d')
    sectionslist = [(x[0], x[1].title) for x in CLASSMAP.items()]
    sectionslist = sorted(sectionslist, key=itemgetter(0))

    context = {
        'title': 'Statistics',
        'navpath': [('Home', '/'), ('Statistics', False)],
        'numrows': numrows,
        'fromtime': fromtime,
        'timeframes': TIMEFRAMES,
        'sectionslist': sectionslist,
    }

    if 'view' in request.GET:
        view = request.GET['view']
        cls = CLASSMAP[view]
        result = cls(fromtime, numrows)
        result.collect()

        context.update({
            'view': view,
            'view_timeframe': dict(TIMEFRAMES)[fromtime],
            'result': result
        })

    return render_to_response('sortedstats/sortedstats.html', context,
                              context_instance=RequestContext(request))
