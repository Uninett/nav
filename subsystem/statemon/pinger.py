#!/usr/bin/python
"""
$Id: pinger.py,v 1.2 2003/06/20 09:34:44 magnun Exp $                                                                                                                              
This file is part of the NAV project.                                                                                             
                                                                                                                                 
Copyright (c) 2002 by NTNU, ITEA nettgruppen                                                                                      
Author: Magnus Nordseth <magnun@stud.ntnu.no>
"""
import os
os.sys.path.append(os.path.split(os.path.realpath(os.sys.argv[0]))[0]+"/lib")
os.sys.path.append(os.path.split(os.path.realpath(os.sys.argv[0]))[0]+"/lib/checker")
os.sys.path.append(os.path.split(os.path.realpath(os.sys.argv[0]))[0]+"/lib/ping")

import megaping, db, config, signal, getopt, time, pwd
import debug
from netbox import Netbox
from output import color

class pinger:
    def __init__(self, **kwargs):
        signal.signal(signal.SIGHUP, self.signalhandler)
        signal.signal(signal.SIGUSR1, self.signalhandler)
        signal.signal(signal.SIGTERM, self.signalhandler)
        self.config=config.pingconf()
        debug.setDebugLevel(int(self.config.get('debuglevel',5)))
        debug.debug("Setting debuglevel=%s "% self.config.get('debuglevel',5))
        self._isrunning=1
        self._looptime=int(self.config.get('checkinterval',60))
        debug.debug("Setting checkinterval=%i" %self._looptime)
        self._debuglevel=0
        self._pidfile=self.config.get('pidfile', 'pinger.pid')
        self.dbconf=config.dbconf()
        self.db=db.db(self.dbconf)
        self.down=[]
        sock = kwargs.get('socket',None)
        self.pinger=megaping.MegaPing(sock)
        self.justStarted = 1
                      
    def getJobs(self):
        """
        Fetches new jobs from the NAV database and appends them to
        the runqueue.
        """
        debug.debug("Getting hosts from database...",7)
        hosts = self.db.hostsToPing()
        self.hosts = []
        for host in hosts:
            netbox = Netbox(*host)
            self.hosts.append(netbox)
        #self.hosts = map(lambda x:x[0], hosts)
        debug.debug("We now got %i hosts in our list to ping" % len(self.hosts),7)

        if self.justStarted:
            for host in self.hosts:
                if host.up != 'y':
                    self.down.append(host)
            debug.debug("%i servers marked as down/service in database" % len(self.down))
            self.justStarted = 0
                

    def main(self):
        """
        Loops until SIGTERM is caught. The looptime is defined
        by self._looptime
        """
        while self._isrunning:
            start=time.time()
            self.getJobs()
            self.pinger.setHosts(self.hosts)
            debug.debug("Starts pinging....",7)
            elapsedtime=self.pinger.start()
            debug.debug("Checks which hosts didn't answer",7)
            down = self.pinger.noAnswers()
            debug.debug("No answer from %i hosts" %len(down),7)
            reportdown = filter(lambda x: x not in self.down, down)
            reportup = filter(lambda x: x not in down, self.down)
            self.down = down

            #Rapporter bokser som har gått ned
            debug.debug("Starts reporting %i hosts as down" % len(reportdown),7)
            for each in reportdown:
                self.db.pingEvent(each, 'DOWN')
                debug.debug("%s marked as down." % each)
            #Rapporter bokser som har kommet opp
            debug.debug("Starts reporting %i hosts as up" % len(reportup),7)
            for each in reportup:
                self.db.pingEvent(each, 'UP')
                debug.debug( "%s marked as up." % each)

            debug.debug("%i hosts checked in %03.3f secs. %i hosts currently marked as down." % (len(self.hosts),elapsedtime,len(self.down)))
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
            pidfile=conf.get('pidfile', 'pinger.pid')
            try:
                pidfile=open(pidfile, 'w')
                pidfile.write(str(pid)+'\n')
                pidfile.close()
            except Exception, e:
                print "Could not open %s" % pidfile
                print str(e)
            os.sys.exit()

        logfile = conf.get('logfile','pinger.log')
        print "Logger til ", logfile
        os.sys.stdout = open(logfile,'a')
        os.sys.stderr = open(logfile,'a')
    myPinger=pinger(socket=sock)
    myPinger.main()


def setUser():
    conf = config.pingconf()
    username = conf.get('user', 'nobody')
    try:
        uid = pwd.getpwnam(username)[2]
        gid = pwd.getpwnam(username)[3]
    except KeyError:
        print "User %s not found" % username
        print "Exiting"
        os.sys.exit()
    print "Setting UID to %s " % uid 
    os.setegid(gid)
    os.seteuid(uid)
    os.umask(0022)
    print "Now running as user %s" % username

if __name__=='__main__':
    try:
        opts, args = getopt.getopt(os.sys.argv[1:], 'hnv', ['help','nofork', 'version'])
        nofork=0

        for opt, val in opts:
            if opt in ('-h','--help'):
                help()
                os.sys.exit()
            elif opt in ('-n','--nofork'):
                nofork=1
            elif opt in ('-v','--version'):
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
