#!/usr/bin/python
"""
$Author: magnun $
$Id: controller.py,v 1.28 2002/11/28 22:07:34 magnun Exp $
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
        self._deamon=kwargs.get("fork", 1)
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


    def createStatusFile(self):
        """
        Dumps the current status to a file.
        """
        try:
            outputfile = open('/var/www/html/services/status.txt','w')
        except:
            print "Failed to open outputfile"

                                                                
        for each in self._jobs:
            try:
                host=self.db.netboxid[each.getBoksid()]
            except KeyError:
                host = "Unspecified host"
            outputfile.write("%-25s %-5s %-5s %s\n" % (host, each.getType(), each.getStatus(), each.getVersion()) )

        outputfile.write("\n\nLast updated: %s" % time.asctime())
        outputfile.close()

                      
    def getJobs(self):
        """
        Fetches new jobs from the NAV database and appends them to
        the runqueue.
        """
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
            #filter(self._runqueue.enq, self._jobs)
            wait=self._looptime - (time.time() - start)
            if self._jobs:
                pause=wait/(len(self._jobs)*2)
            else:
                pause=0
            for each in self._jobs:
                self._runqueue.enq(each)
                time.sleep(pause)
            wait=self._looptime - (time.time() - start)
            self.debug("Waiting %i seconds." % wait)
            self.createStatusFile()
            if wait <= 0:
                self.debug("Only superman can do this. Humans cannot wait for %i seconds." % wait)
            else:
                time.sleep(wait)


    def signalhandler(self, signum, frame):
        if signum == signal.SIGTERM:
            self.debug( "Caught SIGTERM. Exiting.")
            self._runqueue.terminate()
            os.sys.exit(0)
        elif signum == signal.SIGUSR1:
            # reopen the logfile
            logfile=self.conf.get("logfile", "servicemon.log")
            self.debug("Caught SIGUSR1. Reopening logfile...")
            os.sys.stdout.close()
            os.sys.stderr.close()
            os.sys.stdout = open(logfile,'w')
            os.sys.stderr = open(logfile,'w')
            self.debug("Reopened logfile: %s" % logfile)
        else:
            self.debug( "Caught %s. Resuming operation." % (signum))


def start(nofork):
    """
    Forks a new prosess, letting the service run as
    a daemon.
    """
    conf = config.serviceconf()
    if fork:
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
        #print "Logger til ", logfile
        os.sys.stdout = open(logfile,'w')
        os.sys.stderr = open(logfile,'w')

    myController=controller(fork=fork)
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
        fork=1

        for opt, val in opts:
            if opt in ('-h','--help'):
                help()
                os.sys.exit()
            elif opt in ('-n','--nofork'):
                fork=0
            elif opt in ('-v','--version'):
                print __version__
                os.sys.exit(0)
                

    except (getopt.error):
        help()
        os.sys.exit(2)
                               
    start(fork)
