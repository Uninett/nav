#!/usr/bin/env python
# $Id$
#
# Copyright 2006 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# Authors: John Magne Bredal <john.m.bredal@ntnu.no>
#

from mod_python import apache
import nav, nav.path
from nav import web, db
from nav.db import manage
from nav.web.templates.MainTemplate import MainTemplate
from nav.web.URI import URI

import threading
import time
import re

import nav.rrd.presenter
import nav.db

import ConfigParser

#from nav.web.templates import SortedStatsTemplate
import SortedStatsTemplate


totalskip = 0 # The total number of skipped rrd-datasources.
configfile = nav.path.sysconfdir + "/sortedStats.confg"

def handler(req):

    # Some variables
    defaultnumrows = 20
    fromtimes = {'hour': 'Last Hour', 'day': 'Last Day', 'week': 'Last Week', 'month': 'Last Month'}
    defaultfromtime = 'day'

    reload(SortedStatsTemplate)

    page = SortedStatsTemplate.SortedStatsTemplate()

    # Set some page-info
    req.content_type = "text/html"
    req.send_http_header()

    page.path = [("Home","/"), ("Sorted Statistics", False)]
    page.title = "Sorted Statistics"


    # Read configfile, give template config-object.
    config = ConfigParser.ConfigParser()
    config.read(configfile)
    page.config = config


    # TODO: Must verify that the mandatory variables are in the
    # config-file.
    

    # Get args, see what we are supposed to display
    args = URI(req.unparsed_uri)

    numrows = args.get('numrows') or defaultnumrows
    fromtime = args.get('fromtime') or defaultfromtime
    page.numrows = numrows
    page.fromtime = fromtime
    page.fromtimes = fromtimes


    # view is the name of the drop-down menu.
    if args.get('view'):
        view = args.get('view')
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


        # If forcedview is checked, ask getData to get values live.
        forcedview = bool(args.get('forcedview'))
        values, exetime, units, cachetime, cached = getData(forcedview, config.get(view, 'path'), config.get(view, 'dsdescr'), fromtime, view, cachetimeout, modifier)


        page.forcedview = args.get('forcedview')


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
            page.footer = "using cached data"
        else:
            page.footer = "using live data"

        # TODO: Perhaps have an option in the configfile to modify values.
        # modifier: / 8
        # Also manually set units which overrides units gotten from db.
        
    else:
        page.view = ""
        page.showArr = ""
        page.exetime = 0
        page.forcedview = "0"

    req.write(page.respond())
    return apache.OK


def getData(forced, path, dsdescr, fromtime, view, cachetimeout, modifier):
    """

    Fetches data either from cache or live from rrd-files using the
    Presenter-module.

    """

    starttime = time.time()

    # Normalview is a boolean that if true indicates that we may use
    # cached data.

    if not forced:
        # Check if we have data cached 
        b, valuelist, units, epoch = checkCache(view, fromtime, cachetimeout, modifier)

        exetime = "%.2f" %(time.time() - starttime) # Time we used to fetch data from cache
        cachetime = "%.2f" %(time.time() - float(epoch)) # Time since last write of cache

        # If b i true it means we got data from cache, else we fetch
        # live data.

        if b:
            return valuelist, exetime, units, cachetime, True

    cachetime = ""
    
    # threadparameters
    numthreads = 1
    threads = []

    # List with numbers to sort
    valuelist = {}

    # Connect to database
    conn = nav.db.getConnection('default')

    cur = conn.cursor()

    # Values skipped because of 'nan' or 0
    totalskip = 0

    # Query database based on parameters in chosen section
    finddatasources = "SELECT path, rrd_fileid, filename, rrd_datasourceid, units FROM rrd_file LEFT JOIN rrd_datasource USING (rrd_fileid) WHERE path LIKE '%%%s%%' AND descr ~* '%s'" %(path, dsdescr)
    cur.execute(finddatasources)


    dslist = []
    units = ""
    # Put each ds in a dict with descriptor
    for row in cur.dictfetchall():
        units = row['units']
        directory = row['path']
        directory = re.sub(".*/([^\/]+)$", "\\1", directory)
        fileid = row['rrd_fileid']
        filename = directory + "/" + row['filename']
        dslist.append((filename, row['rrd_datasourceid']))


    # Size of slice
    slicesize = len(dslist) / numthreads
    sliceindex = 0

    # Start threads
    for i in range(1, numthreads + 1):
        print "Starting thread %s" %i

        # We slice the dslist into roughly equal sizes and give each
        # thread one slice each.

        slice = []
        if i == numthreads:
            slice = dslist[sliceindex:len(dslist)]
            print "T%s got %s:%s" %(i, sliceindex, len(dslist))
        else: 
            slice = dslist[sliceindex:slicesize+sliceindex]
            print "T%s got %s:%s" %(i, sliceindex, slicesize + sliceindex)
        
        sliceindex += slicesize

        # Start thread
        t = getRRDvalue(i, slice, valuelist, fromtime, modifier)
        threads.append(t)
        t.start()


    # Wait for threads to finish
    for thread in threads:
        thread.join()


    exetime = "%.2f" %(time.time() - starttime) # Time used to fetch data

    saveCache(view, fromtime, valuelist, units)

    # Return list of values
    return valuelist, exetime, units, cachetime, False



def checkCache (view, fromtime, cachetimeout, modifier):
    """
    Checks if values are cached, returns true with list if so,
    otherwise false
    """

    filename = "/tmp/ss_" + view + "_" + fromtime
    valuelist = {}
    units = ""
    epoch = 0

    try:
        f = file(filename, 'r')

        # The two first lines are units and time data was stored, in epoch
        units = f.readline()
        epoch = f.readline()

        # If seconds since last store is greater than timeout set in
        # config-file, return false.

        diff = time.time() - float(epoch)
        if diff > int(cachetimeout):
            return False, valuelist, units, epoch

        # Fill valuelist with values from file
        for line in f:
            key, value = line.split()

            # Apply modifer and eval expression for result
            if modifier:
                value = eval(value + modifier)
            else:
                value = float(value)
                
            valuelist[key] = value

        f.close()
        return True, valuelist, units, epoch

    except IOError:
        return False, valuelist, units, epoch


def saveCache (view, fromtime, valuelist, units):
    """ Saves a cache to file """

    filename = "/tmp/ss_" + view + "_" + fromtime

    units = str(units) or "N/A"
    epoch = "%.f" %(time.time())

    try:
        f = file(filename, 'w')

        f.write(units + "\n")
        f.write(epoch + "\n")

        for v in valuelist.keys():
            f.write(str(v) + " " + str(valuelist[v]) + "\n")

        f.close()
    except IOError:
        pass
        

def sortbyvalue(d):
    """ Returns the keys of dictionary d sorted by their values """

    items = d.items()
    backitems = [ (v[1], v[0]) for v in items ]
    backitems.sort()
    return [ v[1] for v in backitems ]


def formatTime(seconds):
    """ Converts seconds to a string with days, hours, minutes, seconds """

    seconds = int(float(seconds))

    days, seconds = divmod(seconds, 86400)
    hours,seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    #timestring = "%s days, %s hours, %s minutes, %s seconds" %(days, hours, minutes, seconds)
    timestring = "%s:%s:%s" %(hours, minutes, seconds)

    return timestring


# Create a threaded class that queries an rrd-file for a datasource in
# a given interval

class getRRDvalue (threading.Thread):
    """
    This class uses the presenter-module in NAV to fetch values from
    multiple rrd-files in one go. The values returned are put on
    the valuelist-dict.
    """

    def __init__(self, threadid, dslist, valuelist, fromtime, modifier):
        threading.Thread.__init__(self)
        self.threadid = threadid
        self.starttime = time.time()
        self.dslist = dslist
        self.valuelist = valuelist
        self.fromtime = fromtime
        self.modifier = modifier


    def run(self):
        # How many files did we not get a value from
        skip = 0

        # Let the presenter-module fetch value from the rrd-file
        pres = nav.rrd.presenter.presentation()
        filenames = []
        
        # Foreach datasource in the dslist, add it to the presenter list. This way we fetch the values from all datasources at once.
        for slice in self.dslist:
            (filename, dsid) = slice
            
            print "T%s: Got %s, %s from list" %(self.threadid, filename, dsid)
            
            pres.addDs(dsid)
            
            filename = filename.replace(".rrd", "")
            filenames.append(filename)
                

        pres.timeLast(self.fromtime)
        try:
            value = pres.average()            

        except ValueError:
            print "T%s: Could not get values from %s (DS %s)" %(self.threadid, filename, dsid)


        # Reverse filenames-list so that we can pop the list (in stead of shift)
        filenames.reverse()

        for v in value:
            # Put value in a list
            filename = filenames.pop()
            if v == 'nan' or v == 0:
                skip += 1
            else:
                if self.modifier:
                    v = eval (str(v) + self.modifier)
                
            self.valuelist[filename] = v


