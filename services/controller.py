#!/usr/bin/python
"""
$Author: magnun $
$Id: controller.py,v 1.26 2002/09/19 22:21:05 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/controller.py,v $

"""
import os
os.sys.path.append(os.path.split(os.path.realpath(os.sys.argv[0]))[0]+"/lib")
os.sys.path.append(os.path.split(os.path.realpath(os.sys.argv[0]))[0]+"/lib/handler")

import RunQueue, types, time, job, getopt, signal, config, db, debug, mailAlert

class controller:
    def __init__(self, **kwargs):
        signal.signal(signal.SIGHUP, self.signalhandler)
        signal.signal(signal.SIGUSR1, self.signalhandler)
        signal.signal(signal.SIGTERM, self.signalhandler)
        self.conf=config.serviceconf()
        debugger=debug.debug()
        self.debug=debugger.log
        self._isrunning=1
        self._jobs=[]
        self._debuglevel=0
        self._runqueue=RunQueue.RunQueue(controller=self)
        self._pidfile=self.conf.get('pidfile', 'controller.pid')
        self._looptime=int(self.conf.get("checkinterval",60))
        self.debug("Setting checkinterval=%i"% self._looptime)
        self.db=db.db(config.dbconf("db.conf"))
        self.db.start()
        self.alerter=mailAlert.mailAlert()
        self.alerter.start()


                      
    def getJobs(self):
        """
        Fetches new jobs from the NAV database and appends them to
        the runqueue.
        """
        #newjobs = database.getJobs()
        newjobs = self.db.getJobs()


        s=[]    
        for i in newjobs:
            if i in self._jobs:
                s.append(self._jobs[self._jobs.index(i)])
            else:
                s.append(i)

        self._jobs=s
                    
    def main(self):
        """
        Loops until SIGTERM is caught. The looptime is defined
        by self._looptime
        """
        while self._isrunning:
            start=time.time()
            self.getJobs()
            filter(self._runqueue.enq, self._jobs)
            wait=self._looptime - (time.time() - start)
            self.debug("Waiting %i seconds." % wait)
            if wait <= 0:
                self.debug("Only superman can do this. Humans cannot wait for %i seconds." % wait)
            else:
                time.sleep(wait)

    def signalhandler(self, signum, frame):
        if signum == signal.SIGTERM:
            self.debug( "Caught SIGTERM. Exiting.")
            self._runqueue.terminate()
            os.sys.exit(0)
        else:
            self.debug( "Caught %s. Resuming operation." % (signum))


def start(nofork):
    """
    Forks a new prosess, letting the service run as
    a daemon.
    """
    conf = config.serviceconf()
    if not nofork:
        pid=os.fork()
        if pid > 0:
            pidfile=conf.get('pidfile', 'servicemon.pid')
            try:
                pidfile=open(pidfile, 'w')
                pidfile.write(str(pid)+'\n')
                pidfile.close()
            except Exception, e:
                print "Could not open %s" % pidfile
                print str(e)
            os.sys.exit()
                
        logfile = conf.get('logfile','servicemon.log')
        print "Logger til ", logfile
        os.sys.stdout = open(logfile,'w')
        os.sys.stderr = open(logfile,'w')

    myController=controller()
    myController.main()
                



def help():
    print """Service monitor for NAV (Network Administration Visualized).

    Usage: %s [OPTIONS]
    -h  --help      Displays this message
    -n  --nofork    Run in foreground
    -v  --version   Display version and exit


Written by Erik Gorset and Magnus Nordseth, 2002

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
                               
    start(nofork)
