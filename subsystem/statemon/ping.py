#!/usr/bin/env python
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
# $Id: $
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#

import optik
import IPy
import sys
from nav.statemon import megaping

def main():
    usage = "usage: %prog [options] ip-range"
    parser = optik.OptionParser(usage)
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose",
                      help="Verbose output")

    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("incorrect number of arguments")
        sys.exit(1)
    try:
        ips = [str(x) for x in IPy.IP("%s" % args[0])]
        # Remove first and last ip...
        ips.pop(0)
        ips.pop(-1)
    except:
        print "Invalid ip or ip range specified."
        sys.exit(1)

    pinger = megaping.MegaPing()
    pinger.setHosts(ips)
    print "Pinging %s hosts..." % len(ips)
    usedtime = pinger.ping()
    noanswers = pinger.noAnswers()
    if options.verbose:
        for (host, time) in noanswers:
            print "%15s Request timed out..." % host

    answers = pinger.answers()
    #answers.sort()
    for (host, time) in answers:
        print "%15s answers in %3.3fms" % (host, float(time)*1000)

    print "Answer from %s/%s hosts in %s sec" % (len(answers), len(ips), usedtime)
            

if __name__ == '__main__':
    main()
