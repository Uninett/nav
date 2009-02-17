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
# Credits
#

__copyright__ = "Copyright 2008 Norwegian University of Science and Technology"
__license__ = "GPL"
__author__ = "John-Magne Bredal (john.m.bredal@ntnu.no)"

# import regular libraries
import os
import sys
import logging
import ConfigParser

# import nav-libraries
import nav.arnold
import nav.db
import nav.buildconf

"""
t1000 is to be run as a cronjob. It checks the database for any
detained ports. If it finds any, it checks if the mac-address is
active on some other port and detains that port.
"""

def main():

    # Open and read config
    configfile = nav.buildconf.sysconfdir + "/arnold/arnold.conf"
    config = ConfigParser.ConfigParser()
    config.read(configfile)

    # Set variables based on configfile
    loglevel = config.get('loglevel','t1000')
    if not loglevel.isdigit():
        loglevel = logging.getLevelName(loglevel)

    try:
        loglevel = int(loglevel)
    except ValueError:
        loglevel = 20 # default to INFO

    # Create logger, start logging
    logfile = nav.buildconf.localstatedir + "/log/arnold/t1000.log"
    filehandler = logging.FileHandler(logfile)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] ' \
                                  '[%(name)s] %(message)s')
    filehandler.setFormatter(formatter)
    logger = logging.getLogger('t1000')
    logger.addHandler(filehandler)
    logger.setLevel(loglevel)

    logger.info("Starting t1000")

    # Connect to arnold-database, make cursor
    try:
        arnoldconn = nav.db.getConnection('default', 'arnold')
    except nav.db.driver.ProgrammingError, why:
        logger.error("Error connecting to db: %s" %why)

    arnoldc = arnoldconn.cursor()
    
    # Connect to manage-database, make cursor
    try:
        manageconn = nav.db.getConnection('default', 'manage')
    except nav.db.driver.ProgrammingError, why:
        logger.error("Error connecting to db: %s" %why)

    managec = manageconn.cursor()


    # Fetch all mac-addresses that we have detained, check if they are
    # active somewhere else.

    query = """SELECT * FROM identity
    WHERE blocked_status IN ('disabled','quarantined')
    AND lastchanged < now() + '-1 hour'"""

    try:
        arnoldc.execute(query)
    except nav.db.driver.ProgrammingError, why:
        print why


    if arnoldc.rowcount <= 0:
        logger.info("No detained ports in database where lastchanged > 1 hour.")
        sys.exit(0)

    rows = arnoldc.dictfetchall()

    for row in rows:

        logger.info("%s is %s, checking for activity..."
                    %(row['mac'], row['blocked_status']))

        [id] = nav.arnold.findIdInformation(row['mac'], 1)

        logger.debug(id)

        # If this mac-address is active behind another port, block it.
        if id['endtime'] == 'Still Active':

            logger.info("Found active mac")

            # The first thing we do now is to check if this reason is
            # a part of any Blocktype. If it is we need to fetch the
            # vlans from that blocktype, and see if the new ip is on
            # one of those vlans or have to be skipped.

            # Check if part of a blocktype (we assume 1 or nothing)
            q = """SELECT * FROM block WHERE reasonid=%s"""
            arnoldc.execute(q, (row['blocked_reasonid'], ))
            if arnoldc.rowcount > 0:
                blockrow = arnoldc.dictfetchone()

                # Check if new ip is in the vlan ranges. If not
                # continue with the next row
                if blockrow['activeonvlans']:
                    if not isInsideVlans(id['ip'], blockrow['activeonvlans']):
                        logger.info("Ip not in activeonvlans")
                        continue
                    else:
                        logger.debug("Ip in activeonvlans")
                else:
                    logger.debug("No activeonvlans")


            try:
                sw = nav.arnold.findSwportIDinfo(row['swportid'])
            except (nav.arnold.DbError, nav.arnold.PortNotFoundError), why:
                logger.error(why)
                continue


            logger.info("Detaining %s %s:%s"  %(
                sw['sysname'], sw['module'], sw['port']))


            # Find and set autoenable and autoenablestep
            autoenable = 0
            stepq = """SELECT autoenablestep FROM event
            WHERE blocked_reasonid = %s
            AND identityid = %s
            AND autoenablestep IS NOT NULL
            ORDER BY eventtime DESC"""

            try:
                arnoldc.execute(stepq,
                                (row['blocked_reasonid'], row['identityid']))
            except nav.db.driver.ProgrammingError, why:
                logger.error(why)

            autoenablestep = arnoldc.fetchone()[0]
            logger.debug("Setting autoenablestep to %s" %autoenablestep)

            username = os.getlogin()
            comment = "Detained automatically when switching ports"


            # Block or quarantine
            if row['blocked_status'] == 'disabled':
                logger.debug("Trying to disable %s" %row['mac'])
                try:
                    nav.arnold.blockPort(id, sw, autoenable, autoenablestep,
                                         row['determined'],
                                         row['blocked_reasonid'], comment,
                                         username, 'block')
                except (nav.arnold.AlreadyBlockedError,
                        nav.arnold.ChangePortStatusError,
                        nav.arnold.DbError), why:
                    logger.error(why)
            elif row['blocked_status'] == 'quarantined':
                logger.debug("Trying to quarantine %s with vlan %s"
                             %(row['mac'], row['tovlan']))
                try:
                    nav.arnold.blockPort(id, sw, autoenable, autoenablestep,
                                         row['determined'],
                                         row['blocked_reasonid'], comment,
                                         username, 'quarantine', row['tovlan'])
                except (nav.arnold.AlreadyBlockedError,
                        nav.arnold.ChangePortStatusError,
                        nav.arnold.DbError), why:
                    logger.error(why)
                        

        else:
            logger.info("Mac not active.")


def isInsideVlans(ip, vlans):
    """Check if ip is inside the vlans
    vlans: a string with comma-separated vlans.
    """

    # Connect to database
    conn = nav.db.getConnection('default','manage')
    cur = conn.cursor()
    
    # Tidy the vlans-string a bit and create array of it
    vlans = [x.strip() for x in vlans.split(',')]
    
    # For each vlan, check if it is inside the prefix of the vlan.
    for vlan in vlans:

        # This query returns a row if the ip is inside the vlan
        if vlan.isdigit():

            q = """SELECT * FROM prefix LEFT JOIN vlan USING (vlanid)
            WHERE vlan=%s AND %s << netaddr """

            cur.execute(q, (vlan, ip))

            if cur.rowcount > 0:
                return True

    return False


if __name__ == '__main__':
    main()

