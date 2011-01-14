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

import time
from ConfigParser import NoOptionError

from django.http import HttpResponse

from nav.web.templates import SortedStatsTemplate
from . import get_data, sort_by_value, get_configuration

import logging

def index(req):
    """Sorted stats search&result view"""
    logger = logging.getLogger(__name__)
    logger.debug("sortedstats started at %s" %time.ctime())

    # Some variables
    defaultnumrows = 20
    fromtimes = {'hour': 'Last Hour', 'day': 'Last Day', 'week': 'Last Week',
                 'month': 'Last Month'}
    defaultfromtime = 'day'

    page = SortedStatsTemplate.SortedStatsTemplate()

    page.path = [("Home","/"), ("Statistics", False)]
    page.title = "Statistics"

    config = get_configuration()
    page.config = config


    # TODO: Must verify that the mandatory variables are in the
    # config-file.


    # Get args, see what we are supposed to display
    numrows = req.GET.get('numrows', defaultnumrows)
    fromtime = req.GET.get('fromtime', defaultfromtime)
    page.numrows = numrows
    page.fromtime = fromtime
    page.fromtimes = fromtimes


    # view is the name of the drop-down menu.
    if 'view' in req.GET:
        view = req.GET['view']
        page.view = view


        # Cachetimeout is fetched from config-file.
        cachetimeoutvariable = "cachetimeout" + fromtime
        cachetimeout = config.get('ss_general', cachetimeoutvariable)


        # Modifier is an optional variable in the configfile that is
        # used to modify the value we fetch from the rrd-file with a
        # mathematical expression.
        try:
            modifier = config.get(view, 'modifier')
        except NoOptionError:
            modifier = False

        try:
            page.linkview = config.get(view, 'linkview')
        except NoOptionError:
            page.linkview = False

        # If forcedview is checked, ask getData to get values live.
        forcedview = bool(req.GET.get('forcedview', False))
        page.forcedview = req.GET.get('forcedview', None)


        # LOG
        logger.debug ("forcedview: %s, path: %s, dsdescr: %s, fromtime: %s, "
                      "view: %s, cachetimeout: %s, modifier: %s\n"
                      %(str(forcedview), config.get(view, 'path'),
                        config.get(view, 'dsdescr'), fromtime, view,
                        cachetimeout, modifier))


        # Get data
        values, exetime, units, cachetime, cached = \
                get_data(forcedview, config.get(view, 'path'),
                        config.get(view, 'dsdescr'),
                        fromtime, view, cachetimeout, modifier)


        # LOG
        logger.debug("VALUES: %s\n" %(str(values)))


        sorted_keys = sort_by_value(values)
        sorted_keys.reverse()


        # If units are set in the config-file, use it instead of what
        # we find in the database.
        if config.has_option(view, 'units'):
            units = config.get(view, 'units')

        page.exetime = exetime
        page.showArr = values
        page.sortedKeys = sorted_keys
        page.units = units
        if cached:
            page.footer = "using cached data from %s" % (cachetime)
        else:
            page.footer = "using live data"

    else:
        page.view = ""
        page.showArr = ""
        page.exetime = 0
        page.forcedview = "0"


    return HttpResponse(page.respond())


