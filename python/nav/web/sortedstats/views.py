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
import re
import psycopg2.extras

from django.http import HttpResponse

import nav
from nav import web, db
from nav.web.templates.MainTemplate import MainTemplate

import nav.rrd.presenter
import nav.db
import nav.path

import ConfigParser

from nav.web.templates import SortedStatsTemplate
from nav.web.sortedstats import getData, sortbyvalue

import logging

totalskip = 0 # The total number of skipped rrd-datasources.
configfile = nav.path.sysconfdir + "/sortedStats.conf"

# Read configfile
config = ConfigParser.ConfigParser()
config.read(configfile)

def index(req):
    logger = logging.getLogger('nav.web.sortedStats')
    logger.debug("sortedstats started at %s" %time.ctime())

    # Some variables
    defaultnumrows = 20
    fromtimes = {'hour': 'Last Hour', 'day': 'Last Day', 'week': 'Last Week',
                 'month': 'Last Month'}
    defaultfromtime = 'day'

    reload(SortedStatsTemplate)
    page = SortedStatsTemplate.SortedStatsTemplate()

    page.path = [("Home","/"), ("Statistics", False)]
    page.title = "Statistics"


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
        
        modifier = False
        try:
            modifier = config.get(view, 'modifier')
        except:
            pass

        try:
            linkview = config.get(view, 'linkview')
            page.linkview = linkview
        except:
            page.linkview = False
            pass

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
                getData(forcedview, config.get(view, 'path'),
                        config.get(view, 'dsdescr'),
                        fromtime, view, cachetimeout, modifier)


        # LOG
        logger.debug("VALUES: %s\n" %(str(values)))


        sorted = sortbyvalue(values)
        sorted.reverse()


        # If units are set in the config-file, use it instead of what
        # we find in the database. Config.get raises an exception if
        # the option does not exist, this is why we use try...

        try:
            units = config.get(view, 'units')
        except:
            pass

        page.exetime = exetime
        page.showArr = values
        page.sortedKeys = sorted
        page.units = units
        if cached:
            page.footer = "using cached data from %s" %(cachetime)
        else:
            page.footer = "using live data"

    else:
        page.view = ""
        page.showArr = ""
        page.exetime = 0
        page.forcedview = "0"


    return HttpResponse(page.respond())


