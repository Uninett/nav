#!/usr/bin/python
"""
$Id: pinger.py,v 1.1 2002/07/25 16:53:39 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/pinger.py,v $

"""
import os
os.sys.path.append(os.path.split(os.path.realpath(os.sys.argv[0]))[0]+"/lib")
os.sys.path.append(os.path.split(os.path.realpath(os.sys.argv[0]))[0]+"/lib/handler")
os.sys.path.append(os.path.split(os.path.realpath(os.sys.argv[0]))[0]+"/lib/ping")

import megaping, db, debug, config, signal, getopt, time

class pinger:
    def __init__(self, **kwargs):
        signal.signal(signal.SIGHUP, self.signalhandler)
        signal.signal(signal.SIGUSR1, self.signalhandler)
        signal.signal(signal.SIGTERM, self.signalhandler)
        self._isrunning=1
        self._looptime=60
        self._debuglevel=0
        self._pidfile=kwargs.get('pidfile', 'controller.pid')
        self.config=config.config("db.conf")
        self.db=db.db(self.config)
        self.down=[]
        self.pinger=megaping.MegaPing([])
                      
    def getJobs(self):
        """
        Fetches new jobs from the NAV database and appends them to
        the runqueue.
        """

        hosts = self.db.hostsToPing()
        self.hosts = map(lambda x:x[0], hosts)

    def start(self, nofork):
        """
        Forks a new prosess, letting the service run as
        a daemon.
        """
        if nofork:
            self.main()
        else:    
            pid=os.fork()
            if pid > 0:
                try:
                    self._pidfile=open(self._pidfile, 'w')
                    self._pidfile.write(str(pid)+'\n')
                    self._pidfile.close()
                except:
                    print "Could not open %s" % self._pidfile
                os.sys.stdin.close()
                os.sys.stdout.close()
                os.sys.stderr.close()
                os.sys.exit()
            else:
                self.main()

    def main(self):
        """
        Loops until SIGTERM is caught. The looptime is defined
        by self._looptime
        """

        while self._isrunning:
            start=time.time()
            self.getJobs()
            self.pinger.start(self.hosts)
            down = self.pinger.noAnswers()
            reportdown = filter(lambda x: x not in self.down, down)
            reportup = filter(lambda x: x not in down, self.down)
            self.down = down

            #Rapporter bokser som har gått ned
            for each in reportdown:
                self.db.pingEvent(each, 'DOWN')
            #Rapporter bokser som har kommet opp
            for each in reportup:
                self.db.pingEvent(each, 'UP')
                
            time.sleep(20)

    def signalhandler(self, signum, frame):
        if signum == signal.SIGTERM:
            self.debug( "Caught SIGTERM. Exiting.")
            self._runqueue.terminate()
            os.sys.exit(0)
        else:
            self.debug( "Caught %s. Resuming operation." % (signum))




def help():
    print """Paralell pinger for NAV (Network Administration Visualized).

    Usage: %s [OPTIONS]
    -h  --help      Displays this message
    -n  --nofork    Run in foreground
    -v  --version   Display version and exit

    """  % os.path.basename(os.sys.argv[0])


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
                               
    myPinger=pinger()
    myPinger.start(nofork)
