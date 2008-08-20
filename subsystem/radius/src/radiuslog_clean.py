#! /usr/local/bin/python

"""
Author: Roger Kristiansen <roger.kristiansen@gmail.com>
Date:   Apr 05. 2006

Clean out old entries in the log table
"""

import sys
import os
import getopt
from nav import db
from radius_config import *

expiry = LOG_EXPIRY     # How long the records should be kept


try:
    opts, args = getopt.getopt(sys.argv[1:], 'E:')
except getopt.GetoptError, error:
    print >> sys.stderr,error
    sys.exit(1)

for opt, val in opts:
    if opt == '-E':
        # Don't use default expiry time. Strip quotation marks.
        expiry = db.escape(val)[1:][:-1]

connection = db.getConnection(DB_USER, DB)
connection.autocommit(False)
database = connection.cursor()

sqlQuery = "delete from %s where time < NOW() - interval '%s'" % (LOG_TABLE, expiry)

print "Deleting all Radius log records older than %s" % (expiry)

try:
    database.execute(sqlQuery)
    print "%s contains %s expired records." % (LOG_TABLE, database.rowcount)

finally:
    connection.commit()
    print "All expired records deleted"

database.close()
connection.autocommit(True)
