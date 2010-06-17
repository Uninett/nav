#!/usr/bin/env python
#
# Copyright 2008 (C) Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

# Libraries
from optparse import OptionParser
import ConfigParser
import sys, re, os
import getpass
import logging
import psycopg2.extras

# NAV-libraries
from nav.db import getConnection
import nav.arnold
import nav.buildconf


"""
Start Arnold remote via ssh or on the cli via cron. Made for easy use
of arnold-functionality when doing automatic detentions.
NB: This will detain the last port the ip was seen if it is not active.
"""

def main():

    # Read config-file
    configfile = nav.buildconf.sysconfdir + "/arnold/arnold.conf"
    config = ConfigParser.ConfigParser()
    config.read(configfile)

    # Get loglevel from config-file
    loglevel = config.get('loglevel','start_arnold')
    if not loglevel.isdigit():
        loglevel = logging.getLevelName(loglevel)

    try:
        loglevel = int(loglevel)
    except ValueError:
        loglevel = 20 # default to INFO

    # Create logger, start logging
    logfile = nav.buildconf.localstatedir + "/log/arnold/start_arnold.log"

    filehandler = logging.FileHandler(logfile)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] ' \
                                  '[%(name)s] L%(lineno)d %(message)s')
    filehandler.setFormatter(formatter)

    logger = logging.getLogger('start_arnold')
    logger.addHandler(filehandler)
    logger.setLevel(loglevel) 

    logger.info("Starting start_arnold")

    logger.info("Loglevel = %s" %loglevel)

    # Connect to arnold-database
    aconn = getConnection('default', 'arnold')
    acur = aconn.cursor(cursor_factory=psycopg2.extras.DictCursor)


    # Get options from commandline
    usage = """usage: %prog [options] id
Pipe in id's to block or use the -f option to specify file"""
    parser = OptionParser(usage)
    parser.add_option("-i", dest = "blockid", help = "id of blocktype to use")
    parser.add_option("-f", dest = "filename",
                      help = "filename with id's to detain")
    parser.add_option("--list", action = "store_true", dest = "listblocktypes",
                      help = "list predefined detentions")

    (opts, args) = parser.parse_args()

    if opts.listblocktypes:
        format = "%3s %-3s %s"
        print format  %("ID", "Act", "Title")
        acur.execute("SELECT * FROM block ORDER BY blockid")
        for row in acur.fetchall():
            print format %(row['blockid'], row['active'], row['blocktitle'])

        sys.exit()


    # Make sure we have a blockid to work with
    if not opts.blockid:
        print "Please supply an id of a predefined detention."
        logging.debug("Exited due to no blockid")
        sys.exit()
        

    # Fetch options for this blocktype from database
    q = """SELECT * FROM block
    LEFT JOIN blocked_reason ON (reasonid=blocked_reasonid)
    LEFT JOIN quarantine_vlans USING (quarantineid)
    WHERE blockid = %s"""
    acur.execute(q, (opts.blockid, ))


    # Exit if this id does not exist
    if acur.rowcount < 1:
        print "This predefined detention does not exist: %s" %opts.blockid
        logger.debug("Exited due to no such id in database: %s" %opts.blockid)
        sys.exit()

    blockinfo = acur.fetchone()


    # If this predefined detention is not active, print that and exit.
    if blockinfo['active'] == 'n':
        print "This predefined detention is set to inactive. Activate it by editing it on the web."
        logger.debug("Exited due to inactive predefined detention: %s"
                     %opts.blockid)
        sys.exit()


    # Get user running the script. We don't use os.getlogin as this may fail
    # when piping in stuff.
    username = getpass.getuser()
    

    # If we have a filename, try to read file and handle lines there, if not
    # read from stdin.
    ids = []
    if opts.filename:
        # Read from file
        try:
            f = open(opts.filename, 'r')
        except IOError, e:
            print "Error when opening %s: %s" %(opts.filename, e[1])
            logger.error(e)
            sys.exit()
                
        ids = handleLines(f.readlines())
    else:
        # Read from stdin
        ids = handleLines(sys.stdin.readlines())


    # List of successfully blocked ip-addresses
    blocked = []

    # Try to block all id's that we got
    for candidate, comment in ids:
        if not comment:
            comment = ''
        
        logger.debug("Trying to block %s" %candidate)
        print "%s - " %(candidate) ,
        # Find information for each candidate
        try:
            id = nav.arnold.findIdInformation(candidate, 1)
        except (nav.arnold.NoDatabaseInformationError,
                nav.arnold.UnknownTypeError), e:
            print e
            logger.error(e)
            continue

        # findIdInformation returns a list of dicts. As we only query for one,
        # use that one
        id = id[0]

        try:
            sw = nav.arnold.findSwportinfo(id['netboxid'], id['ifindex'],
                                           id['module'])
        except Exception, e:
            print e
            logger.error(e)
            continue


        # We must check if the predefined detention has activeonvlans
        # set. If so, make sure the ipaddress is inside the defined
        # vlans.
        if blockinfo['activeonvlans']:
            ipaddress = id['ip']
            if not isInsideVlans(logger,ipaddress, blockinfo['activeonvlans']):
                logger.info("%s is not inside defined vlanrange for this \
                predefined detention" %ipaddress)
                print "is not in the defined vlans for this detention."
                continue


        # Detain according to detainmenttype
        if blockinfo['detainmenttype'] == 'disable':

            try:
                # block port with info from db
                nav.arnold.blockPort(id, sw, blockinfo['blocktime'], 0,
                                     blockinfo['determined'],
                                     blockinfo['reasonid'],
                                     comment,
                                     username, 'block' )
            except (nav.arnold.InExceptionListError,
                    nav.arnold.WrongCatidError,
                    nav.arnold.DbError, nav.arnold.AlreadyBlockedError,
                    nav.arnold.ChangePortStatusError,
                    nav.arnold.BlockonTrunkError), why:
                print "failed: %s" %why
                logger.error(why)
                continue

        else:

            try:
                # quarantine port with info from db
                nav.arnold.blockPort(id, sw, blockinfo['blocktime'], 0,
                                     blockinfo['determined'],
                                     blockinfo['reasonid'],
                                     comment,
                                     username, 'quarantine', blockinfo['vlan'])
            except (nav.arnold.InExceptionListError,
                    nav.arnold.WrongCatidError,
                    nav.arnold.DbError, nav.arnold.AlreadyBlockedError,
                    nav.arnold.ChangePortStatusError,
                    nav.arnold.BlockonTrunkError), why:
                print "failed: %s" %why
                logger.error(why)
                continue

        print "detained"
        logger.info("%s detained successfully" %candidate)
        blocked.append(id['ip'])


    # For all ports that are detained, group by contactinfo and send mail
    if blockinfo['mailfile'] and len(blocked) > 0:
        print "Sending mail"
        logger.debug("Grouping contacts and ip-addresses")
        manageconn = getConnection('default')
        managecur = manageconn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Send mail to contact address for all ip-addresses that were detained

        contacts = {}

        # First find and group all email-addresses
        for ip in blocked:
            dns = nav.arnold.getHostName(ip)
            netbios = nav.arnold.getNetbios(ip)
            if netbios == 1:
                netbios = ""
            
            # Find contact address
            getcontact = """SELECT * FROM prefix
            LEFT JOIN vlan USING (vlanid)
            LEFT JOIN org USING (orgid)
            WHERE inet '%s' << netaddr AND nettype = 'lan'
            """ %(ip)

            managecur.execute(getcontact)

            if managecur.rowcount <= 0:
                print "No contactinfo for %s in database" %ip
                logger.info("No orginfo in db, can't send mail")

            # For each contact that matches this address, add the ip,
            # dns and netbios name to the contact.
            for orgdict in managecur.fetchall():
                email = orgdict['contact']
                if not email:
                    print "Field contact is empty in database"
                    logger.info("Field contact is empty in database")
                    continue
                # The field may contain several addresses
                splitaddresses = email.split(',')
                splitaddresses = [x.strip() for x in splitaddresses]

                # Put the ip on the contactlist
                for contact in splitaddresses:
                    if contact in contacts:
                        contacts[contact].append([ip,dns,netbios])
                    else:
                        contacts[contact] = [[ip,dns,netbios]]



        # Open mailfile
        try:
            mailfile = open(nav.buildconf.sysconfdir + \
                            "/arnold/mailtemplates/" + blockinfo['mailfile'])
        except IOError, e:
            print e
            logger.error(e)
            sys.exit()

        textfile = mailfile.read()

        # For each contact, send mail with list of blocked ip-adresses on that
        # prefix
        for (contact, iplist) in contacts.items():
            logger.info("Sending mail to %s" %contact)
            
            fromaddr = 'noreply'
            toaddr = contact
            reason = blockinfo['name']
            subject = "Computers detained because of %s" %reason

            msg = textfile
            msg = re.sub('\$reason', reason, msg)
            #msg = re.sub('\$comment', comment, msg)
            msg = re.sub('\$list', "\n".join([" ".join(x) for x in iplist]),
                         msg)

            print msg
            
            try:
                nav.arnold.sendmail(fromaddr, toaddr, subject, msg)
            except Exception, e:
                logger.error(e)
                print e
                continue
            


###############################################################################
# handleLines
def handleLines(lines):
    """
    Read all lines and use the first word in the line as an
    id to detain.
    """
    idlist = []
    
    for line in lines:
        # Skip comments
        if re.match('#', line):
            continue
        
        # "chomp"
        if line and line[-1] == '\n':
            line = line[:-1]

        # Grab first part of line, use that as id to block. Grab the rest and
        # use it as comment
        m = re.match("([^ ]+)(\s+.+)?", line)
        if m:
            id, comment = m.groups()
            if comment:
                comment.strip()
            idlist.append((id,comment))

    return idlist



###############################################################################
# isInsideVlans

def isInsideVlans(logger, ip, vlans):
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

        logger.info(vlan)
        # This query returns a row if the ip is inside the vlan
        if vlan.isdigit():

            q = """SELECT * FROM prefix LEFT JOIN vlan USING (vlanid)
            WHERE vlan=%s AND %s << netaddr """

            logger.info(q)

            cur.execute(q, (vlan, ip))

            if cur.rowcount > 0:
                return True

    return False



if __name__ == '__main__':
    main()
