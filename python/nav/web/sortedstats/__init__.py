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
"""Sorted statistics tool

AKA "ranked statistics".

"""
import os
import time
import logging
import ConfigParser
import psycopg2.extras

import nav.db
import nav.rrd.presenter

def get_data(forced, path, dsdescr, fromtime, view, cachetimeout, modifier):
    """
    Fetches data either from cache or live from rrd-files using the
    Presenter-module.
    """
    logger = logging.getLogger(__name__)
    starttime = time.time()

    # Normalview is a boolean that if true indicates that we may use
    # cached data.

    if not forced:
        # Check if we have data cached
        (data_was_from_cache, valuelist, units, epoch
         ) = check_cache(view, fromtime, cachetimeout)

        # Time we used to fetch data from cache
        exetime = "%.2f" % (time.time() - starttime)
        # Time since last write of cache
        cachetime = time.ctime(float(epoch))

        if data_was_from_cache:
            # Apply modifier if any
            if modifier:
                for k in valuelist.keys():
                    valuelist[k] = eval (str(valuelist[k]) + modifier)
            return valuelist, exetime, units, cachetime, True

    cachetime = ""

    # List with numbers to sort
    valuelist = {}

    # Connect to database
    conn = nav.db.getConnection('default')

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Query database based on parameters in chosen section
    finddatasources = """
    SELECT path, rrd_fileid, filename, rrd_datasourceid, units
    FROM rrd_file
    LEFT JOIN rrd_datasource USING (rrd_fileid)
    WHERE path LIKE '%%%s%%'
    AND netboxid IS NOT NULL AND descr ~* '%s'""" % (path, dsdescr)
    cur.execute(finddatasources)


    # LOG
    logger.debug("Query for data: %s\n" %(finddatasources))

    dslist = []
    units = ""
    # Put each ds in a dict with descriptor
    for row in cur.fetchall():
        units = row['units']
        directory = row['path']
        filename = directory + "/" + row['filename']
        dslist.append((filename, row['rrd_datasourceid']))


    get_rrd_values(dslist, valuelist, fromtime)

    exetime = "%.2f" % (time.time() - starttime) # Time used to fetch data

    save_cache(view, fromtime, valuelist, units)

    # Apply modifier if any
    if modifier:
        for k in valuelist.keys():
            valuelist[k] = eval (str(valuelist[k]) + modifier)

    # Return list of values
    return valuelist, exetime, units, cachetime, False



def check_cache (view, fromtime, cachetimeout):
    """
    Checks if values are cached, returns true with list if so,
    otherwise false
    """

    filename = "/tmp/ss_" + view + "_" + fromtime
    valuelist = {}
    units = ""
    epoch = 0

    try:
        cache_file = file(filename, 'r')

        # The two first lines are units and time data was stored, in
        # epoch
        units = cache_file.readline()
        epoch = cache_file.readline()

        # If seconds since last store is greater than timeout set in
        # config-file, return false.

        diff = time.time() - float(epoch)
        if diff > int(cachetimeout):
            return False, valuelist, units, epoch

        # Fill valuelist with values from file
        for line in cache_file:
            line = line.rstrip()
            key, value = line.split(';;')

            value = float(value)

            valuelist[key] = value

        cache_file.close()
        return True, valuelist, units, epoch

    except IOError:
        return False, valuelist, units, epoch


def save_cache(view, fromtime, valuelist, units):
    """ Saves a cache to file """

    filename = "/tmp/ss_" + view + "_" + fromtime

    units = str(units) or "N/A"
    epoch = "%.f" % (time.time())

    try:
        cache_file = file(filename, 'w')

        cache_file.write(units + "\n")
        cache_file.write(epoch + "\n")

        for key in valuelist.keys():
            cache_file.write(str(key) + ";;" + str(valuelist[key]) + "\n")

        cache_file.close()
    except IOError:
        return


def sort_by_value(dictionary):
    """
    Returns the keys of dictionary sorted by their values
    """

    items = dictionary.items()
    backitems = [ (v[1], v[0]) for v in items ]
    backitems.sort()
    return [ v[1] for v in backitems ]


def format_time(seconds):
    """
    Converts seconds to a string with days, hours, minutes, seconds
    """

    seconds = int(float(seconds))

    days,    seconds = divmod(seconds, 86400)
    hours,   seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    timestring = "%s:%s:%s" % (hours, minutes, seconds)

    return timestring


def get_rrd_values(dslist, valuelist, fromtime):
    """ Get rrd-value from the datasources listed in the dslist. """

    # How many files did we not get a value from
    skip = 0

    # Let the presenter-module fetch value from the rrd-file
    pres = nav.rrd.presenter.presentation()
    filenames = []

    logger = logging.getLogger(__name__)
    logger.debug("dslist: %s\n" %str(dslist))


    # Foreach datasource in the dslist, add it to the presenter
    # list. This way we fetch the values from all datasources at once.
    for slicepart in dslist:
        (filename, dsid) = slicepart

        logger.debug("Got %s, %s from list" %(filename, dsid))

        pres.addDs(dsid)

        filename = filename.replace(".rrd", "")
        filenames.append(filename)

    pres.timeLast(fromtime)

    try:
        values = pres.average()
        logger.debug("Values: %s" %(str(values)))

    except ValueError, (errstr):
        logger.debug("Could not average values %s" %(errstr))
        return


    # Reverse filenames-list so that we can pop the list (in stead of
    # shift)
    filenames.reverse()

    for value in values:
        # Put value in a list
        #(filename,dsid) = filenames.pop()
        filename = filenames.pop()
        if value == 'nan' or value == 0 or value == '':
            skip += 1
        else:
            valuelist[filename] = value

        logger.debug("Putting %s on %s" % (value, filename))

def get_configuration():
    """Reads and returns the config file as a ConfigParser object"""
    configfile = os.path.join(nav.path.sysconfdir,
                              "sortedStats.conf")
    config = ConfigParser.ConfigParser()
    config.read(configfile)
    return config
