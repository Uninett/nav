#!/usr/bin/env python
# -*- coding: ISO8859-1 -*-
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
"""Delete old arp and cam records from the NAV database.

Usage: navclean.py [options...]

Unless options are given, the number of expired ARP/CAM records will
be printed.  The default expiry limit is 6 months.  To actually delete
the expired records, add the -f option.

Available options are:

  -h, --help    -- Show this help screen.
  -q            -- Be quiet.
  -f            -- Force deletion of expired records.
  -e <date>     -- Set a different expiry date (default is 6 months
                   ago) on ISO format.
  -E <interval> -- Set a different expiry date using PostgreSQL
                   interval syntax.  E.g.: '30 days', '4 weeks', '6
                   months'
"""
__id__ = "$Id$"

import sys
import getopt
import nav.db
import psycopg

def main(args):
    """ Main execution function."""
    global quiet, force, expiry
    quiet = False
    force = False
    expiry = "NOW() - interval '6 months'"
    
    try:
        opts, args = getopt.getopt(args, 'hqfe:E:', ['help'])
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
            
    cx = nav.db.getConnection('default', 'manage')
    # Perform deletions inside a transaction, so that we may rollback
    # if -n was specified on command line.
    cx.autocommit(0)
    cursor = cx.cursor()

    selector = "WHERE end_time < %s" % expiry
    sumtotal = 0

    for table in ('arp', 'cam'):
        sql = 'DELETE FROM %s %s' % (table, selector)
        try:
            cursor.execute(sql)
            if not quiet:
                print "%s contains %s expired records." % (table, cursor.rowcount)
            sumtotal += cursor.rowcount
        except psycopg.ProgrammingError, e:
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
            print "Expired records deleted."

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
