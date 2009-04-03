#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004 Norwegian University of Science and Technology
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
# This script will help remove old arp/cam records from the NAV
# database.  It could also be extended to perform other database
# maintenance tasks in NAV.
#
# Authors: Morten Vold <morten.vold@itea.ntnu.no>
#
"""Delete old arp, cam or radius accounting records from the NAV database.

Usage: navclean.py [options...]

Unless options are given, the number of expired records will be printed
The default expiry limit is 6 months. The -e and -E sets a common expiry
date for all tables. If you want different expiry dates for each table,
you need to run navclean more than once. To actually delete the expired
records, add the -f option.

Available options are:

  -h, --help    -- Show this help screen.
  -q            -- Be quiet.
  -f            -- Force deletion of expired records.
  -e <date>     -- Set a different expiry date (default is 6 months
                   ago) on ISO format.
  -E <interval> -- Set a different expiry date using PostgreSQL
                   interval syntax.  E.g.: '30 days', '4 weeks', '6
                   months'
  --arp         -- Delete from ARP table
  --cam         -- Delete from CAM table
  --radiusacct  -- Delete from radius accounting table
  --radiuslog   -- Delete from radius error log table

"""
__id__ = "$Id: navclean.py 2875 2004-07-14 09:51:24Z mortenv $"

import sys
import getopt
import nav.db
import psycopg2

def main(args):
    """ Main execution function."""
    global quiet, force, tables, radiusAcctTable
    quiet = False
    force = False
    expiry = "NOW() - interval '6 months'"
    radiusAcct = False
    radiusAcctTable = "radiusacct"
    radiusLogTable = "radiuslog"
 
    tables = []
   
    try:
        opts, args = getopt.getopt(args, 'hqfe:E:', ['help', 'arp', 'cam', 'radiusacct', 'radiuslog'])
    except getopt.GetoptError, error:
        print >> sys.stderr, error
        usage()
        sys.exit(1)

    for opt,val in opts:
        if opt == '-h':
            usage()
            sys.exit(0)
        if opt == '-q':
            quiet = True
        if opt == '-f':
            force = True
        if opt == '-e':
            expiry = nav.db.escape(val)
        if opt == '-E':
            expiry = "NOW() - interval %s" % nav.db.escape(val)
        if opt == '--arp':
            tables.append("arp")
        if opt == '--cam':
            tables.append("cam")
        if opt == '--radiusacct':
            tables.append("radiusacct")
        if opt == '--radiuslog':
            tables.append("radiuslog")

    cx = nav.db.getConnection('default', 'manage')
    # Perform deletions inside a transaction, so that we may rollback
    # if -n was specified on command line.
    cx.autocommit(0)
    cursor = cx.cursor()
    sumtotal = 0


    arpCamSelector = "WHERE end_time < %s" % expiry
    radiusAcctSelector = """WHERE (acctstoptime < %s) 
                    OR ((acctstarttime + (acctsessiontime * interval '1 sec')) < %s)
                    OR (acctstarttime < %s AND (acctstarttime + (acctsessiontime * interval '1 sec')) IS NULL)
""" % (expiry, expiry, expiry)
    radiusLogSelector = "WHERE time < %s" % expiry

    for table in tables:
        if table == "arp" or table == "cam":
            selector = arpCamSelector
        if table == radiusAcctTable:
            selector = radiusAcctSelector
        if table == radiusLogTable:
            selector = radiusLogSelector

        sql = 'DELETE FROM %s %s' % (table, selector)
        
        try:
            cursor.execute(sql)
            if not quiet:
                print "%s contains %s expired records." % (table, cursor.rowcount)
            sumtotal += cursor.rowcount

        except psycopg2.ProgrammingError, e:
            print >> sys.stderr, "The PostgreSQL backend produced a ProgrammingError.\n" + \
                  "Most likely, your expiry specification is invalid: %s" % expiry;
            cx.rollback()
            sys.exit(1)


    if not force:
        cx.rollback()
        sumtotal = 0
    else:
        cx.commit()

        if not quiet and sumtotal > 0:
            print "Expired ARP/CAM/Radius Acccounting records deleted."

    if not quiet and sumtotal == 0: print "None deleted."

    cx.close()


def usage():
    """ Print a usage screen to stderr."""
    print >> sys.stderr, __doc__

##############
# begin here #
##############
if __name__ == '__main__':
    main(sys.argv[1:])
