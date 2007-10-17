#!/usr/bin/env python
#
# Copyright 2007 UNINETT AS
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


# Libraries
from optparse import OptionParser
import ConfigParser
import sys, re

# NAV-libraries
from nav.db import getConnection
import nav.arnold
import nav.buildconf


"""
Start Arnold remote via ssh or on the cli via cron. Made for easy use
of arnold-functionality when doing automatic blocks.
"""

def main():

    # Read config-file
    configfile = nav.buildconf.sysconfdir + "/arnold/arnold.conf"
    config = ConfigParser.ConfigParser()
    config.read(configfile)

    # Connect to arnold-database
    dbname = config.get('arnold','database')
    aconn = getConnection('default', dbname)
    acur = aconn.cursor()

    # Get options from commandline
    usage = """usage: %prog [options] id
Pipe in id's to block or use the -f option to specify file"""
    parser = OptionParser(usage)
    parser.add_option("-i", dest = "blockid", help = "id of blocktype to use")
    parser.add_option("-f", dest = "filename", help = "filename with id's to block")
    parser.add_option("--list", action = "store_true", dest = "listblocktypes", help = "list blocktypes")

    (opts, args) = parser.parse_args()

    if opts.listblocktypes:
        format = "%3s %s"
        print format  %("ID", "Title")
        acur.execute("SELECT * FROM block")
        for row in acur.dictfetchall():
            print format %(row['blockid'], row['blocktitle'])

        sys.exit(0)

    # Fetch options for this blocktype from database
    if opts.blockid:
        q = "SELECT * FROM block WHERE blockid = %s"
        acur.execute(q, (opts.blockid, ))

        blockinfo = acur.dictfetchone()

        # Format input
        ids = []
        if opts.filename:
            ids = handleFile(opts.filename)
        else:
            # Read from stdin
            ids = handleStdin(sys.stdin)
            pass

        # Try to block all id's that we got
        for candidate in ids:
            id = nav.arnold.findIdInformation(candidate, 1)
            sw = nav.arnold.findSwportinfo(id['netboxid'], id['ifindex'], id['module'], id['port'])
            try:
                nav.arnold.blockPort(id, sw, blockinfo['autoenable'], 0, blockinfo['determined'], blockinfo['reasonid'], 'Blocktype %s' %blockinfo['blocktitle'], os.getlogin())
            except (InExceptionListError, WrongCatidError, DbError, AlreadyBlockedError, ChangePortStatusError), why:
                print why
                continue


def handleFile(file):
    """
    Read from a file, put first word in file in a list
    """

    try:
        lines = file.readlines()
    except Exception, e:
        print e

    idlist = []
        
    for line in lines:
        # "chomp"
        if line and line[-1] == '\n':
            line = line[:-1]

        # Grab first part of line, put it in list
        if re.match("[^ ]+", line):
            id = re.match("([^ ]+)", line).groups()[0]
            idlist.append(id)

    return idlist


def handleStdin(stream):
    """
    Parse stdin and put candidates in a list
    """

    


if __name__ == '__main__':
    main()
