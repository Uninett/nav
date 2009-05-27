#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
# Copyright 2002-2004 Norwegian University of Science and Technology
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
"""
Pings multiple hosts in parallel
"""

import os
import sys
import signal
import getopt
import time
import pwd

import nav.daemon
from nav.daemon import safesleep as sleep
from nav.statemon import rrd
from nav.statemon import megaping
from nav.statemon import db
from nav.statemon import config
from nav.statemon import circbuf
from nav.statemon import debug
from nav.statemon.event import Event
from nav.statemon.netbox import Netbox

class pinger:
    def __init__(self, **kwargs):
        signal.signal(signal.SIGHUP, self.signalhandler)
        signal.signal(signal.SIGTERM, self.signalhandler)
        self.config=config.pingconf()
        debug.setDebugLevel(int(self.config.get("debuglevel",5)))
        debug.debug("Setting debuglevel=%s "% self.config.get("debuglevel",5))
        self._isrunning=1
        self._looptime=int(self.config.get("checkinterval",60))
        debug.debug("Setting checkinterval=%i" %self._looptime)
        self._debuglevel=0
        self.db=db.db()
        sock = kwargs.get("socket",None)
        self.pinger=megaping.MegaPing(sock)
        self._nrping = int(self.config.get("nrping" ,3))
        # To keep status...
        self.netboxmap = {} # hash netboxid -> netbox
        self.down = []      # list of netboxids down
        self.replies = {}      # hash netboxid -> circbuf
        self.ipToNetboxid = {}
                      
    def updateHostList(self):
        """
        Fetches all netboxes from the NAVdb, and updates
        internal data structures.
        """
        debug.debug("Getting hosts from database...",7)
        hosts = self.db.hostsToPing()
        netboxmap = {}
        self.ipToNetboxid = {}
        for host in hosts:
            netboxid, deviceid, sysname, ip, up = host
            netbox = Netbox(netboxid, deviceid, sysname, ip, up)
            if not self.netboxmap.has_key(netbox.netboxid):
                # new netbox. Be sure to get it's state
                if netbox.up != 'y':
                    debug.debug("Got new netbox, %s, currently "
                                "marked down in navDB" % netbox.ip, 7)
                    self.down.append(netbox.netboxid)
            if not self.replies.has_key(netbox.netboxid):
                self.replies[netbox.netboxid] = circbuf.CircBuf()
                if netbox.up != 'y':
                    buf = self.replies[netbox.netboxid]
                    # This genious line marks all-down for the whole buf
                    map(buf.push, [-1]*len(buf))
            netboxmap[netbox.netboxid]=netbox
            self.ipToNetboxid[netbox.ip] = netbox.netboxid
        # Update netboxmap
        self.netboxmap = netboxmap
        debug.debug("We now got %i hosts in our list to ping" % 
                    len(self.netboxmap), 7)
        #then update our pinger object
        self.pinger.setHosts(self.ipToNetboxid.keys())

    def generateEvents(self):
        """
        Report state changes to event engine.
        """
        debug.debug("Checks which hosts didn't answer",7)
        answers = self.pinger.results()
        for ip, rtt in answers:
            # rtt = round trip time (-1 => host didn't reply)
            netboxid = self.ipToNetboxid.get(ip)
            self.replies[netboxid].push(rtt)
            netbox = self.netboxmap[netboxid]
            if rtt != -1:
                rrd.update(netbox.netboxid, netbox.sysname, 'N', 'UP', rtt)
            else:
                # ugly...
                rrd.update(netbox.netboxid, netbox.sysname, 'N', 'DOWN', 5)

        downNow = []
        # Find out which netboxes to consider down
        for (netboxid, replies) in self.replies.items():
            if replies[:self._nrping] == [-1]*self._nrping:
                downNow.append(netboxid)
        
        debug.debug("No answer from %i hosts" %len(downNow),7)
        # Detect state changes since last run
        reportDown = filter(lambda x: x not in self.down, downNow)
        reportUp = filter(lambda x: x not in downNow, self.down)
        self.down = downNow

        # Reporting netboxes as down
        debug.debug("Starts reporting %i hosts as down" % len(reportDown),7)
        for netboxid in reportDown:
            netbox = self.netboxmap[netboxid]
            newEvent = Event(0,
                             netbox.netboxid,
                             netbox.deviceid,
                             Event.boxState,
                             "pping",
                             Event.DOWN
                             )
            self.db.newEvent(newEvent)
            debug.debug("%s marked as down." % netbox)
        # Reporting netboxes as up
        debug.debug("Starts reporting %i hosts as up" % len(reportUp),7)
        for netboxid in reportUp:
            try:
                netbox = self.netboxmap[netboxid]
            except:
                debug.debug("Netbox %s is no longer with us..." % netboxid)
                continue
            newEvent = Event(0,
                             netbox.netboxid,
                             netbox.deviceid,
                             Event.boxState,
                             "pping",
                             Event.UP
                             )
            self.db.newEvent(newEvent)
            debug.debug( "%s marked as up." % netbox)

    def main(self):
        """
        Loops until SIGTERM is caught.
        """
        self.db.start()
        while self._isrunning:
            start=time.time()
            debug.debug("Starts pinging....", 7)
            self.updateHostList()
            elapsedtime=self.pinger.ping()
            self.generateEvents()
            debug.debug("%i hosts checked in %03.3f secs. %i hosts "
                        "currently marked as down." %
                        (len(self.netboxmap), elapsedtime, len(self.down)))
            wait=self._looptime-elapsedtime
            if wait > 0:
                debug.debug("Sleeping %03.3f secs" % wait,6)
            else:
                wait=abs(self._looptime + wait)
                debug.debug("Check lasted longer than looptime. "
                            "Delaying next check for %03.3f secs" % wait,2)
            sleep(wait)

    def signalhandler(self, signum, frame):
        if signum == signal.SIGTERM:
            debug.debug("Caught SIGTERM. Exiting.",1)
            sys.exit(0)
        elif signum == signal.SIGHUP:
            # reopen the logfile
            logfile=self.config.get("logfile", "pping.log")
            debug.debug("Caught SIGHUP. Reopening logfile...")
            sys.stdout.close()
            sys.stderr.close()
            sys.stdout = open(logfile,'a')
            sys.stderr = open(logfile,'a')
            debug.debug("Reopened logfile: %s" % logfile)
        else:
            debug.debug( "Caught %s. Resuming operation." % (signum),2)




def help():
    print """Paralell pinger for NAV (Network Administration Visualized).
    
    Usage: %s [OPTIONS]
    -h  --help      Displays this message
    -n  --nofork    Run in foreground
    -v  --version   Display version and exit

    Written by Stian Søiland and Magnus Nordseth, 2002
    """  % os.path.basename(sys.argv[0])

def start(nofork):
    """
    Forks a new prosess, letting the service run as
    a daemon.
    """
    conf = config.pingconf()
    pidfilename = conf.get("pidfile","/usr/local/nav/var/run/pping.pid")

    # Already running?
    try:
        nav.daemon.justme(pidfilename)
    except nav.daemon.AlreadyRunningError, e:
        otherpid = file(pidfilename, "r").read().strip()
        sys.stderr.write("pping is already running (pid: %s)\n" % otherpid)
        sys.exit(1)
    except nav.daemon.DaemonError, e:
        sys.stderr.write("%s\n" % e)
        sys.exit(1)
        
    if not nofork:
        nav.daemon.daemonize(pidfilename)
    
        logfile = conf.get("logfile","pping.log")
        sys.stdout = open(logfile,"a")
        sys.stderr = open(logfile,"a")

    myPinger=pinger(socket=sock)
    myPinger.main()


def setUser():
    conf = config.pingconf()
    username = conf.get("user", "nobody")
    nav.daemon.switchuser(username)

if __name__=="__main__":
    nofork=0
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "hnv",
                                   ["help","nofork", "version"])
        for opt, val in opts:
            if opt in ("-h","--help"):
                help()
                sys.exit(0)
            elif opt in ("-n","--nofork"):
                nofork=1
            elif opt in ("-v","--version"):
                print __version__
                sys.exit(0)
                
    except (getopt.error):
        help()
        sys.exit(2)
    if os.getuid() != 0:
        print "Must be started as root"
        sys.exit(1)
    sock = megaping.makeSocket()
    setUser()
    start(nofork)
