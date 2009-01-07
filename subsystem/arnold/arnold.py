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


from optparse import OptionParser
import ConfigParser
import logging
import os, sys, re
import getpass

# NAV libraries
import nav.buildconf
import nav.arnold
from nav.db import getConnection

# Paths
configfile = nav.buildconf.sysconfdir + "/arnold/arnold.conf"
logfile = nav.buildconf.localstatedir + "/log/arnold/arnold.log"


"""
The arnold-script is mainly made for emergencyuse only. It does not
have all the functionality of the webinterface nor is it very
userfriendly. We strongly recommend using the webinterface for serious
arnolding. It is however good to use when running cron-jobs for
blocking.
"""


def main():

    # Read config
    config = ConfigParser.ConfigParser()
    config.read(configfile)

    # Define options
    usage = "usage: %prog [options] id"
    parser = OptionParser(usage)
    parser.add_option("-s", dest="state", help="state: enable, disable or \
quarantine")
    parser.add_option("-f", "--file", dest="inputfile",
                      help="File with stuff to disable.")
    parser.add_option("--listreasons", action="store_true", dest="listreasons",
                      help="List reasons for blocking in database.")
    parser.add_option("-l", "--listblocked", action="store_true",
                      dest="listblocked", help="List blocked ports.")
    parser.add_option("-v", dest="vlan", help="The vlan to change ports to - \
must be set if state is quarantine")
    parser.add_option("-r", dest="reason", help="Reason for this action")
    parser.add_option("-c", dest="comment", help="Comment")
    parser.add_option("--autoenable", dest="autoenable",
                      help="Days to autoenable")
    parser.add_option("--determined", action="store_true", dest="determined",
                      help="Flag for determined blocking")

    (opts, args) = parser.parse_args()


    # Get loglevel from config-file
    loglevel = config.get('loglevel','arnold')
    if not loglevel.isdigit():
        loglevel = logging.getLevelName(loglevel)

    try:
        loglevel = int(loglevel)
    except ValueError:
        loglevel = 20 # default to INFO


    # Create logger, start logging
    filehandler = logging.FileHandler(logfile)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] ' \
                                  '[%(name)s] L%(lineno)d %(message)s')
    filehandler.setFormatter(formatter)

    logger = logging.getLogger('arnold')
    logger.addHandler(filehandler)
    logger.setLevel(loglevel)

    logger.info("Starting arnold")
    logger.info("Loglevel = %s" %loglevel)


    # If file is given, assume we are disabling everything in the
    # file. The file may contain a mixture of ip, mac or swportid's
    # (I admit I could have used more functions to clean up the code)
    if opts.inputfile:

        if not opts.reason:
            logger.info("User did not define reason for block")
            parser.error("Please specify a reason for the block")
            
        if opts.state == 'quarantine' and not opts.vlan:
            logger.info("User did not define vlan to change to")
            parser.error("Please specify a vlan to change to")

        
        try:
            # open file, get input
            f = file (opts.inputfile)
            handleFile(f, opts)
        except IOError, why:
            logger.error(why)
            print why
            sys.exit(1)


    elif opts.listreasons:
        try:
            reasons = nav.arnold.getReasons()
            for r in reasons:
                print "%2s: %s - %s" \
                      %(r['blocked_reasonid'], r['name'], r['comment'])
        except nav.arnold.DbError, why:
            logger.error(why)
            print why
            sys.exit(1)

    elif opts.listblocked:
        conn = getConnection('default', 'arnold')
        c = conn.cursor()

        q = """SELECT identityid, mac, ip, netbios, blocked_status AS status
        FROM identity
        WHERE blocked_status IN ('disabled','quarantined')
        ORDER BY lastchanged"""

        try:
            c.execute(q)
        except nav.db.driver.ProgrammingError, why:
            logger.error(why)
            print why
            sys.exit(1)
            
        if c.rowcount > 0:
            rows = c.dictfetchall()
            format = "%-4s %-15s %-17s %-16s %s"
            print format  %('ID','IP','MAC', 'NETBIOS','STATUS')
            for row in rows:
                print format %(row['identityid'], row['ip'],
                               row['mac'], row['netbios'], row['status'])
        else:
            print "No blocked ports in arnold"


    elif opts.state:

        if len(args) < 1:
            logger.info("User did not specify any arguments")
            parser.error("I need an ip, mac or databaseid to have " \
                         "something to do.")

        if not opts.state in ['enable','disable','quarantine']:
            logger.info("User did not specify correct state: %s" %opts.state)
            parser.error("State must be either enable, disable or quarantine")

        # Enable or disable interface based on input from user
        res = ""
        if opts.state == 'enable':
            for id in args:
                logger.info("Running openPort (%s, %s)" %(id, getpass.getuser()))

                # Open port
                try:
                    nav.arnold.openPort(id, getpass.getuser())
                except (nav.arnold.NoDatabaseInformationError,
                        nav.arnold.DbError,
                        nav.arnold.ChangePortStatusError), why:
                    print why
                    logger.error(why)
                    continue

        elif opts.state in ['disable','quarantine']:

            if not opts.reason:
                logger.info("User did not define reason for block")
                parser.error("Please specify a reason for the block")

            if opts.state == 'quarantine' and not opts.vlan:
                logger.info("User did not define vlan to change to")
                parser.error("Please specify a vlan to change to")


            # Loop through the id's to block
            for id in args:

                # Find information about switch and id in database
                try:
                    res = nav.arnold.findIdInformation(id, 3)
                except (nav.arnold.NoDatabaseInformationError,
                        nav.arnold.UnknownTypeError,
                        nav.arnold.PortNotFoundError), why:
                    logger.error(why)
                    print why
                    continue

                swportids = []
                counter = 1


                format = "%-2s %-19s %-15s %-17s %s (%s:%s)"
                print format %('ID','Lastseen','IP','MAC','Switch',
                               'module','port')


                # Store information about the switchport
                swinfo = {}

                # Print all ports the id has been active on
                for i in res:
                    try:
                        swinfo[counter] = nav.arnold.findSwportinfo(i['netboxid'],
                                                                    i['ifindex'],
                                                                    i['module'])
                        
                    except (nav.arnold.NoDatabaseInformationError,
                            nav.arnold.UnknownTypeError,
                            nav.arnold.PortNotFoundError), why:
                        print why
                        logger.error(why)
                        continue
                        
                    swportids.append(swinfo[counter]['swportid'])
                    
                    print format %(counter, i['endtime'], i['ip'], i['mac'],
                                   i['sysname'], i['module'], i['port'])
                    counter = counter + 1


                # If no port is found in database, report and exit
                if len(swportids) < 1:
                    print "Could not find any port where %s has been active" \
                          %id
                    logger.info("Could not find any port where %s has \
                    been active" %id)
                    sys.exit()
                    
                # If id is not active, ask user if he really wants to
                # block anyway
                
                swportids.sort()
                try:
                    idstring = ", ".join([str(x) for x in range(1,counter)])
                    answer = raw_input("Choose which one to block (%s) " \
                                       "0 = skip:  " %idstring)
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

                    logger.info("Blocking %s (%s:%s)" %(res[answer]['sysname'],
                                                        res[answer]['module'],
                                                        res[answer]['port']))
                    print "Blocking %s (%s:%s)" %(res[answer]['sysname'],
                                                  res[answer]['module'],
                                                  res[answer]['port'])

                if opts.state == 'disable':
                    # Do snmp-set to block port
                    try:
                        nav.arnold.blockPort(res[answer], swinfo[answer+1],
                                             opts.autoenable, 0,
                                             opts.determined,
                                             opts.reason, opts.comment,
                                             getpass.getuser(), 'block')
                    except (nav.arnold.ChangePortStatusError,
                            nav.arnold.AlreadyBlockedError,
                            nav.arnold.FileError,
                            nav.arnold.InExceptionListError,
                            nav.arnold.WrongCatidError), why:
                        print why
                        logger.error(why)
                            
                elif opts.state == 'quarantine':
                    # Set vlan specified
                    try:
                        nav.arnold.blockPort(res[answer], swinfo[answer+1],
                                             opts.autoenable, 0,
                                             opts.determined,
                                             opts.reason, opts.comment,
                                             getpass.getuser(), 'quarantine',
                                             opts.vlan)
                    except (nav.arnold.ChangePortVlanError,
                            nav.arnold.AlreadyBlockedError,
                            nav.arnold.FileError,
                            nav.arnold.InExceptionListError,
                            nav.arnold.WrongCatidError), why:
                        print why
                        logger.error(why)
                                
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
    

def handleFile(file, opts):
    """
    Reads a file line by line. Parses the first word (everything that
    is not a space) of a file and tries to use that as an id in a
    block. NB: Make sure the first character of a line is not a space.
    """

    lines = file.readlines()

    for line in lines:
        # "chomp"
        if line and line[-1] == '\n':
            line = line[:-1]

        # Grab first part of line, run it through findIdInformation to
        # see if it is a valid id
        if re.match("[^ ]+", line):
            id = re.match("([^ ]+)", line).groups()[0]
            print "Trying to block id %s" %id
            try:
                info = nav.arnold.findIdInformation(id, 2)
            except (nav.arnold.UnknownTypeError,
                    nav.arnold.NoDatabaseInformationError), why:
                print why
                continue

            if len(info) > 0:

                firstlist = info[0]

                # Check end-time of next list to see if this one is
                # also active. If both are active, continue as we
                # don't know what to block
                if info[1]['endtime'] == 'Still Active':
                    print "Active on two or more ports, don't know " \
                          "which one to block. Skipping this id."
                    continue

                swlist = nav.arnold.findSwportinfo(firstlist['netboxid'],
                                                   firstlist['ifindex'],
                                                   firstlist['module'])

                autoenable = opts.autoenable
                autoenablestep = 0
                determined = opts.determined
                reason = opts.reason
                comment = opts.comment
                username = getpass.getuser()

                if opts.state == 'disable':

                    try:
                        nav.arnold.blockPort(firstlist, swlist, autoenable,
                                             autoenablestep, determined,
                                             reason, comment, username,
                                             'block')
                    except (nav.arnold.ChangePortStatusError,
                            nav.arnold.InExceptionListError,
                            nav.arnold.WrongCatidError,
                            nav.arnold.DbError,
                            nav.arnold.AlreadyBlockedError), why:
                        print why

                elif opts.state == 'quarantine':
                    
                    try:
                        nav.arnold.blockPort(firstlist, swlist, autoenable,
                                             autoenablestep, determined,
                                             reason, comment, username,
                                             'quarantine', opts.vlan)
                    except (nav.arnold.ChangePortStatusError,
                            nav.arnold.InExceptionListError,
                            nav.arnold.WrongCatidError,
                            nav.arnold.DbError,
                            nav.arnold.AlreadyBlockedError), why:
                        print why
                        

if __name__ == '__main__':
    main()
