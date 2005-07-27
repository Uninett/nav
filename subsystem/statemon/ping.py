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
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#          Stian Soiland <stain@itea.ntnu.no>
#

import sys
import socket
try:
    from optparse import OptionParser
except ImportError:
    from optik import OptionParser    
import IPy
from nav.statemon import debug
# ignore "lack of config file"
debug.setDebugLevel(1)
from nav.statemon import megaping

def resolve(host):
    try:
        resolved = socket.gethostbyaddr(host)
        return resolved[0]
    except socket.herror:
        return host    

def main():
    usage = "usage: %prog [options] ip-range [..]"
    parser = OptionParser(usage)
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose",
                      help="Verbose output")
    parser.add_option("-r", "--resolve",
                      action="store_true", dest="resolve",
                      help="Resolve DNS")
    parser.add_option("-u", "--up",
                      action="store_true", dest="up",
                      help="Only print hosts that are up")
    parser.add_option("-d", "--down",
                      action="store_true", dest="down",
                      help="Only print hosts that are down")

    (options, args) = parser.parse_args()
    if not args:
        parser.error("incorrect number of arguments")
        sys.exit(1)
    ips = []    
    while args:    
        try:
            moreips = [str(x) for x in IPy.IP("%s" % args.pop())]
        except:
            parser.error("Invalid ip or ip range specified.")
            sys.exit(2)
        else:
            if len(moreips) > 2:
                # Skip network address and broadcast 
                moreips.pop(0)
                moreips.pop(-1)
            ips.extend(moreips)
    if options.up and options.down:
        parser.error("Pointless to combine --up and --down")    

    pinger = megaping.MegaPing()
    pinger.setHosts(ips)
    if options.verbose:
        print >>sys.stderr, "Pinging %s hosts..." % len(ips)
    usedtime = pinger.ping()
    noanswers = pinger.noAnswers()
    if options.verbose or options.down:
        for (host, time) in noanswers:
            if options.resolve:
                host = resolve(host)
                format = "%s Request timed out..."
            else:
                format = "%15s Request timed out..."    
            if options.down:
                format = "%s"
            print format % host

    answers = pinger.answers()
    for (host, time) in answers:
        if options.resolve:
            host = resolve(host)
        if options.up:
            print host
        elif options.down:
            pass    
        else:
            print "%15s answers in %3.3fms" % (host, float(time)*1000)

    if options.verbose:
        print >>sys.stderr, "Answer from %s/%s hosts in %s sec" % (
                            len(answers), len(ips), usedtime)
            

if __name__ == '__main__':
    main()
