#!/usr/bin/env python
#
# Copyright 2008 Norwegian University of Science and Technology
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
# Authors: John-Magne Bredal <john.m.bredal@ntnu.no>
#

__copyright__ = "Copyright 2008 Norwegian University of Science and Technology"
__license__ = "GPL"
__author__ = "John-Magne Bredal (john.m.bredal@ntnu.no)"

# import regular libraries
import os
import sys
import logging
import ConfigParser
import getpass

import psycopg2.extras

# import nav-libraries
import nav.arnold
import nav.db
import nav.buildconf

"""
autoenable is meant to be run as a cronjob. It checks the configured
arnold-database for any detained ports and opens them if they have a
autoenable-time set and that time has passed.
"""

def main():

    # Open and read config
    configfile = nav.buildconf.sysconfdir + "/arnold/arnold.conf"
    config = ConfigParser.ConfigParser()
    config.read(configfile)

    # Set variables based on configfile

    loglevel = config.get('loglevel','autoenable')
    if not loglevel.isdigit():
        loglevel = logging.getLevelName(loglevel)

    try:
        loglevel = int(loglevel)
    except ValueError:
        loglevel = 20 # default to INFO

    # Create logger, start logging
    logfile = nav.buildconf.localstatedir + "/log/arnold/autoenable.log"
    filehandler = logging.FileHandler(logfile)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] ' \
                                  '[%(name)s] L%(lineno)d %(message)s')
    filehandler.setFormatter(formatter)
    logger = logging.getLogger('autoenable')
    logger.addHandler(filehandler)
    logger.setLevel(loglevel)

    logger.info("Starting autoenable")

    # Connect to arnold-database configured in arnold.conf
    try:
        arnoldconn = nav.db.getConnection('default', 'arnold')
    except nav.db.driver.ProgrammingError, why:
        logger.error("Could not connect to arnolddatabase: %s" %why)
    
    arnoldc = arnoldconn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Connect to manage-database
    try:
        manageconn = nav.db.getConnection('default','manage')
    except nav.db.driver.ProgrammingError, why:
        logger.error("Could not connect to manage-db: %s" %why)
    
    managec = manageconn.cursor()


    # Get all blocked port where autoenable is < now
    query = """SELECT identityid, swportid, ip, mac
    FROM identity
    WHERE autoenable < now()
    AND blocked_status IN ('disabled','quarantined')
    """

    arnoldc.execute(query)

    if arnoldc.rowcount <= 0:
        logger.info("No ports ready for opening.")
        sys.exit(0)

    # For each port that is blocked, try to enable the port.
    for row in arnoldc.fetchall():

        try:
            swinfo = nav.arnold.findSwportIDinfo(row['swportid'])
        except nav.arnold.PortNotFoundError, why:
            logger.error(why)
            continue

        # Open port
        try:
            nav.arnold.openPort(row['identityid'], getpass.getuser(),
                                eventcomment="Opened automatically by \
                                autoenable")
            logger.info("Opening %s %s:%s for %s" %(
                swinfo['sysname'], swinfo['module'],
                swinfo['port'], row['mac']))
        except (nav.arnold.NoDatabaseInformationError,
                nav.arnold.ChangePortStatusError,
                nav.arnold.DbError), why:
            logger.error(why)
            continue


if __name__ == '__main__':
    main()
