#!/usr/bin/python
"""
$Id: pinger.py,v 1.2 2003/06/20 09:34:44 magnun Exp $
This file is part of the NAV project.

Copyright (c) 2002 by NTNU, ITEA


Author: Magnus Nordseth <magnun@stud.ntnu.no>
"""

LIBDIR="/usr/local/nav/navme/lib/python"
import os
if LIBDIR not in os.sys.path:
    os.sys.path.append(LIBDIR)

import signal
import getopt
import time
import pwd

from nav.statemon import rrd
from nav.statemon import megaping
from nav.statemon import db
from nav.statemon import config
from nav.statemon import circbuf
from nav.statemon import debug
from nav.statemon.netbox import Netbox
from nav.statemon.output import color


class pinger:
    def __init__(self, **kwargs):
        signal.signal(signal.SIGHUP, self.signalhandler)
        signal.signal(signal.SIGUSR1, self.signalhandler)
        signal.signal(signal.SIGTERM, self.signalhandler)
        self.config=config.pingconf()
        debug.setDebugLevel(int(self.config.get("debuglevel",5)))
        debug.debug("Setting debuglevel=%s "% self.config.get("debuglevel",5))
        self._isrunning=1
        self._looptime=int(self.config.get("checkinterval",60))
        debug.debug("Setting checkinterval=%i" %self._looptime)
        self._debuglevel=0
        self.dbconf=config.dbconf()
        self.db=db.db(self.dbconf)
        sock = kwargs.get("socket",None)
        self.pinger=megaping.MegaPing(sock)
        self._nrping = 3 
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
        debug.debug("We now got %i hosts in our list to ping" % len(self.netboxmap),7)
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

        #Rapporter bokser som har gått ned
        debug.debug("Starts reporting %i hosts as down" % len(reportDown),7)
        for netboxid in reportDown:
            netbox = self.netboxmap[netboxid]
            self.db.pingEvent(netbox, "DOWN")
            debug.debug("%s marked as down." % netbox)
        #Rapporter bokser som har kommet opp
        debug.debug("Starts reporting %i hosts as up" % len(reportUp),7)
        for netboxid in reportUp:
            try:
                netbox = self.netboxmap[netboxid]
            except:
                debug.debug("Netbox %s is no longer with us..." % netboxid)
                continue
            self.db.pingEvent(netbox, "UP")
            debug.debug( "%s marked as up." % netbox)

    def main(self):
        """
        Loops until SIGTERM is caught.
        """
        while self._isrunning:
            start=time.time()
            debug.debug("Starts pinging....",7)
            self.updateHostList()
            elapsedtime=self.pinger.ping()
            self.generateEvents()
            debug.debug("%i hosts checked in %03.3f secs. %i hosts currently marked as down." % (len(self.netboxmap),elapsedtime,len(self.down)))
            wait=self._looptime-elapsedtime
            if wait > 0:
                debug.debug("Sleeping %03.3f secs" % wait,6)
            else:
                wait=abs(self._looptime + wait)
                debug.debug("Check lasted longer than looptime. Delaying next check for %03.3f secs" % wait,2)
            time.sleep(wait)

    def signalhandler(self, signum, frame):
        if signum == signal.SIGTERM:
            debug.debug("Caught SIGTERM. Exiting.",1)
            os.sys.exit(0)
        else:
            debug.debug( "Caught %s. Resuming operation." % (signum),2)




def help():
    #print """Paralell pinger for NAV (Network Administration Visualized).
    #
    #Usage: %s [OPTIONS]
    #-h  --help      Displays this message
    #-n  --nofork    Run in foreground
    #-v  --version   Display version and exit

    #Written by Stian Søiland and Magnus Nordseth, 2002
    #"""  % os.path.basename(os.sys.argv[0]))
    print color("Parallel pinger for NAV (Network Administration Visualized).","white")
    print
    print "Usage : %s [OPTIONS]" % os.path.basename(os.sys.argv[0])
    print color("-h  --help   ", "green"), "Displays this message"
    print color("-n  --nofork ", "green"), "Run in foreground"
    print color("-v  --version", "green"), "Display version and exit"
    print
    print
    print "Written by Stian Søiland and Magnus Nordseth, 2002"
    print




def start(nofork):
    """
    Forks a new prosess, letting the service run as
    a daemon.
    """
    conf = config.pingconf()
    if not nofork:
        pid=os.fork()
        if pid > 0:
            os.sys.exit()
        logfile = conf.get("logfile","pping.log")
        os.sys.stdout = open(logfile,"a")
        os.sys.stderr = open(logfile,"a")
    myPinger=pinger(socket=sock)
    myPinger.main()


def setUser():
    conf = config.pingconf()
    username = conf.get("user", "nobody")
    try:
        uid = pwd.getpwnam(username)[2]
        gid = pwd.getpwnam(username)[3]
    except KeyError:
        print "User %s not found" % username
        print "Exiting"
        os.sys.exit()
    os.setegid(gid)
    os.seteuid(uid)
    os.umask(0022)

if __name__=="__main__":
    nofork=0
    try:
        opts, args = getopt.getopt(os.sys.argv[1:],
                                   "hnv",
                                   ["help","nofork", "version"])
        for opt, val in opts:
            if opt in ("-h","--help"):
                help()
                os.sys.exit()
            elif opt in ("-n","--nofork"):
                nofork=1
            elif opt in ("-v","--version"):
                print __version__
                os.sys.exit(0)
                
    except (getopt.error):
        help()
        os.sys.exit(2)
    if os.getuid() != 0:
        print "Must be started as root"
        os.exit(0)
    sock = megaping.makeSocket()
    setUser()
    start(nofork)
