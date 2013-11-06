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

import re
import time
from operator import itemgetter
from itertools import islice
from ConfigParser import NoOptionError

from django.shortcuts import render_to_response
from django.template import RequestContext

from . import get_data, get_configuration

import logging


TIMEFRAMES = (
    ('hour', 'Last Hour'),
    ('day', 'Last Day'),
    ('week', 'Last Week'),
    ('month', 'Last Month'),
)

TARGET = re.compile('cricket-data(/.*)')
OUTPUT = re.compile('.*/([^/]+/[^/]+)$')


def index(request):
    """Sorted stats search & result view"""
    logger = logging.getLogger(__name__)
    logger.debug('sortedstats started at %s' % time.ctime())

    numrows = int(request.GET.get('numrows', 20))
    fromtime = request.GET.get('fromtime', 'day')

    config = get_configuration()

    # TODO: Use namedtuple for more expressive templates?
    sectionslist = [
        (
            section,
            config.get(section, 'name'),
        )
        for section in sorted(config.sections())
        if section != 'ss_general'
    ]

    context = {
        'title': 'Statistics',
        'navpath': [('Home', '/'), ('Statistics', False)],
        'numrows': numrows,
        'fromtime': fromtime,
        'timeframes': TIMEFRAMES,
        'sectionslist': sectionslist,
        'exetime': 0,
    }

    if 'view' in request.GET:
        view = request.GET['view']
        viewname = config.get(view, 'name')

        cachetimeout = config.get('ss_general', 'cachetimeout' + fromtime)

        # Modifier is an optional variable in the configfile that is
        # used to modify the value we fetch from the rrd-file with a
        # mathematical expression.
        try:
            modifier = config.get(view, 'modifier')
        except NoOptionError:
            modifier = False

        try:
            linkview = config.get(view, 'linkview')
        except NoOptionError:
            linkview = False

        # If forcedview is checked, ask getData to get values live.
        forcedview = bool(request.GET.get('forcedview', False))

        logger.debug('forcedview: %s, path: %s, dsdescr: %s, fromtime: %s, '
                     'view: %s, cachetimeout: %s, modifier: %s\n'
                     % (forcedview, config.get(view, 'path'),
                     config.get(view, 'dsdescr'), fromtime, view,
                     cachetimeout, modifier))

        values, exetime, units, cachetime, cached = get_data(
            forcedview,
            config.get(view, 'path'),
            config.get(view, 'dsdescr'),
            fromtime, view, cachetimeout, modifier)

        logger.debug('VALUES: %s\n' % (str(values)))

        # Make a list of (key, value) tuples from values dict, taking
        # the first 'numrows' elements sorted by value
        values_sorted = islice(sorted(values.iteritems(), key=itemgetter(1),
                                      reverse=True), numrows)

        values_formatted = [
            (
                TARGET.search(key).group(1),
                OUTPUT.sub('\\1', key),
                '{0:.2f}'.format(value)
            ) for key, value in values_sorted
        ]

        # If units are set in the config-file, use it instead of what
        # we find in the database.
        if config.has_option(view, 'units'):
            units = config.get(view, 'units')

        if cached:
            footer = 'using cached data from {0}'.format(cachetime)
        else:
            footer = 'using live data'

        context.update({
            'view': view,
            'viewname': viewname,
            'view_timeframe': dict(TIMEFRAMES)[fromtime],
            'linkview': linkview,
            'forcedview': forcedview,
            'values': values_formatted,
            'exetime': exetime,
            'units': units,
            'footer': footer,
        })

    return render_to_response('sortedstats/sortedstats.html', context,
                              context_instance=RequestContext(request))
