#!/usr/bin/python
"""
$Author: erikgors $
$Id: controller.py,v 1.7 2002/06/13 15:47:18 erikgors Exp $
$Source: /usr/local/cvs/navbak/navme/services/controller.py,v $

"""

import RunQueue, types, os, time, job, getopt, signal,database

class controller:
    def __init__(self, **kwargs):
        signal.signal(signal.SIGHUP, self.signalhandler)
        signal.signal(signal.SIGUSR1, self.signalhandler)
        signal.signal(signal.SIGTERM, self.signalhandler)
        self._runqueue=RunQueue.RunQueue(controller=self)
        self._isrunning=1
        self._jobs=[]
        self._looptime=60
        self._pidfile=kwargs.get('pidfile', 'controller.pid')

    def getJobs(self):
        """
        Fetches new jobs from the NAV database and appends them to
        the runqueue.
        """
        newjobs = database.getJobs()
            
        s=[]    
        for i in newjobs:
            if i in self._jobs:
                s.append(self._jobs[self._jobs.index(i)])
            else:
                s.append(i)

        self._jobs=s
                    

    def debug(self, msg):
        """
        Provides simple debug support. Should we use syslog or
        a file?
        """
        if type(msg)==types.StringType:
            print (time.strftime('%d %b %Y %H:%M:%S ', time.localtime())) + msg

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
                self._pidfile=open(PIDFILE, 'w')
                self._pidfile.write(str(pid)+'\n')
                self._pidfile.close()
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
	database.startup('host = localhost user = manage dbname = manage password = eganam')
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




def help():
    print """Service monitor for NAV (Network Administration Visualized).

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
            if opt == '-h' or opt == '--help':
                help()
                os.sys.exit()
            elif opt == '-n' or opt == '--nofork':
                nofork=1
            elif opt == '-v' or opt == '--version':
                print __version__
                os.sys.exit(0)
                

    except (getopt.error):
        help()
        os.sys.exit(2)
                               
    controller=controller()
    controller.start(nofork)
