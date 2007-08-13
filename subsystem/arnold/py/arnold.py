#!/usr/bin/env python
#
# Copyright 2006 UNINETT AS
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

__copyright__ = "Copyright 2007 UNINETT AS"
__license__ = "GPL"
__author__ = "John-Magne Bredal (john.m.bredal@ntnu.no)"


from optparse import OptionParser
import ConfigParser
import logging
import os, sys, re

# NAV libraries
import nav.buildconf
import nav.arnold
from nav.db import getConnection

# Temp
from pysnmp import v1, v2c, asn1, role

# Paths
configfile = nav.buildconf.sysconfdir + "/arnold.conf"
logfile = nav.buildconf.localstatedir + "/log/arnold.log"


"""
The arnold-script is mainly made for emergencyuse only. It has not all
the functionality of the webinterface nor is it very userfriendly. We
strongly recommend using the webinterface for serious arnolding. It is
however good to use when running cron-jobs for blocking.
"""


def main():

    # Read config
    config = ConfigParser.ConfigParser()
    config.read(configfile)

    # Define options
    usage = "usage: %prog [options] id"
    parser = OptionParser(usage)
    parser.add_option("-s", dest="state", help="state: enable or disable")
    parser.add_option("-f", "--file", dest="inputfile", help="File with stuff to disable.")
    parser.add_option("--listreasons", action="store_true", dest="listreasons", help="List reasons for blocking in database.")
    parser.add_option("-l", "--listblocked", action="store_true", dest="listblocked", help="List blocked ports.")
    parser.add_option("-v", dest="vlan", help="The vlan to change ports to")
    parser.add_option("-r", dest="reason", help="Reason for this action")
    parser.add_option("-c", dest="comment", help="Comment")
    parser.add_option("--autoenable", dest="autoenable", help="Days to autoenable")
    parser.add_option("--determined", action="store_true", dest="determined", help="Flag for determined blocking")

    (opts, args) = parser.parse_args()

    # If file is given, assume we are disabling everything in the
    # file. The file may contain a mixture of ip, mac or swportid's
    if opts.inputfile:
        try:
            # open file, get input
            f = file (opts.inputfile)
            handleFile(f)
        except IOError, why:
            logger.error(why)
            sys.exit(1)


    elif opts.listreasons:
        try:
            reasons = nav.arnold.getReasons()
            for r in reasons:
                print "%2s: %s" %(r['blocked_reasonid'], r['text'])
        except DbError, why:
            print why
            sys.exit(1)

    elif opts.listblocked:
        conn = getConnection('default','arnold')
        c = conn.cursor()

        q = "SELECT identityid, mac, ip, lastchanged FROM identity WHERE blocked_status = 'disabled' ORDER BY lastchanged"

        try:
            c.execute(q)
        except nav.db.driver.ProgrammingError, why:
            print why
            sys.exit(1)

        if c.rowcount > 0:
            rows = c.dictfetchall()
            format = "%-4s %-15s %-15s %s"
            print format  %('ID','IP','MAC','LASTCHANGED')
            for row in rows:
                print format %(row['identityid'], row['ip'], row['mac'], row['lastchanged'])
        else:
            print "No blocked ports in arnold"


    elif opts.state:

        if len(args) < 1:
            parser.error("We need an ip, mac or swportid or databaseid to do something with.")

        if not opts.state in ['enable','disable']:
            parser.error("State must be either enable or disable")


        # Enable or disable interface based on input from user
        res = ""
        if opts.state == 'enable':
            for id in args:
                # Open port
                try:
                    nav.arnold.openPort(id, os.getlogin())
                except (nav.arnold.NoDatabaseInformationError, nav.arnold.DbError, nav.arnold.ChangePortStatusError), why:
                    print why
                    continue
                

        elif opts.state == 'disable':

            # Loop through the id's to block
            for id in args:

                # Find information about switch and id in database
                try:
                    res = nav.arnold.findIdInformation(id, 3)
                except (nav.arnold.NoDatabaseInformationError, nav.arnold.UnknownTypeError, nav.arnold.PortNotFoundError), why:
                    print why
                    continue

                if res == 1:
                    continue

                swportids = []
                counter = 1

                # Print all ports the id has been active on
                for i in res:
                    try:
                        swinfo = nav.arnold.findSwportinfo(i['netboxid'], i['ifindex'], i['module'], i['port'])
                    except (nav.arnold.NoDatabaseInformationError, nav.arnold.UnknownTypeError, nav.arnold.PortNotFoundError), why:
                        print why
                        continue
                        
                    swportids.append(swinfo['swportid'])
                    
                    print "%s [%s] %s (%s): %s (%s:%s)" %(
                        counter, i['endtime'], i['ip'], i['mac'], i['sysname'], i['module'], i['port'])
                    counter = counter + 1


                # If no port is found in database, report and exit
                if len(swportids) < 1:
                    print "Could not find any port where %s has been active" %id
                    sys.exit()
                    
                # If id is not active, ask user if he really wants to block anyway
                swportids.sort()
                try:
                    answer = raw_input("Choose which one to block (%s) 0 = skip:  " %", ".join([str(x) for x in range(1,counter)]))
                except KeyboardInterrupt:
                    print "\nExited by user"
                    sys.exit(1)


                if not answer.isdigit() or int(answer) >= counter:
                    print "No such id listed"
                    continue
                elif int(answer) == 0:
                    continue
                else:
                    answer = int(answer) - 1
                    print "Blocking %s (%s:%s)" %(res[answer]['sysname'], res[answer]['module'], res[answer]['port'])

                # Do snmp-set to block port
                try:
                    nav.arnold.blockPort(res[answer], swinfo, opts.autoenable, 0, opts.determined, opts.reason, opts.comment, os.getlogin())
                except (nav.arnold.ChangePortStatusError, nav.arnold.AlreadyBlockedError, nav.arnold.FileError, nav.arnold.InExceptionListError), why:
                    print why

    else:

        print "You must either choose state or give a file as input."
        sys.exit(1)

    # There are three ways to give input to arnold
    # 1. ip-address
    # 2. mac-address
    # 3. swportid

    # When done with disabling or enabling, do the following:
    # - send mail to those affected by the action if configured
    # - print status to STDOUT for reading from web
    


    

if __name__ == '__main__':
    main()
