#!/usr/bin/env python

import nav.arnold
import nav.db
import os
import sys

# Connect to arnold-database
arnoldconn = nav.db.getConnection('default','arnold')
arnoldc = arnoldconn.cursor()

# Connect to manage-database
manageconn = nav.db.getConnection('default','manage')
managec = manageconn.cursor()


# Get all blocked port where autoenable is < now
query = "SELECT identityid, swportid, ip, mac FROM identity WHERE autoenable < now() AND blocked_status ='disabled'"
arnoldc.execute(query)

if arnoldc.rowcount <= 0:
    print "No ports ready for opening."
    sys.exit(0)


for row in arnoldc.dictfetchall():

    try:
        swinfo = nav.arnold.findSwportIDinfo(row['swportid'])
    except nav.arnold.PortNotFoundError, why:
        print why

    # Open port
    try:
        nav.arnold.openPort(row['identityid'], os.getlogin())
        print "Opening %s %s:%s blocking %s" %(swinfo['sysname'], swinfo['module'], swinfo['port'], row['mac'])
    except (nav.arnold.NoDatabaseInformationError, nav.arnold.ChangePortStatusError, nav.arnold.DbError), why:
        print why
        continue
