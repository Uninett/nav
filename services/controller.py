#!/usr/bin/env python
"""
$Author: magnun $
$Id: controller.py,v 1.1 2002/06/09 23:14:55 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/controller.py,v $

"""

import RunQueue, types, os

class controller:
    def __init__(self):
        self._runqueue=RunQueue.RunQueue()

    def debug(self, msg):
        """
        Provides simple debug support. Should we use syslog or
        a file?
        """
        if type(msg)==types.StringType:
            print (time.strftime('%d %b %Y %H:%M:%S ', time.localtime())) + msg

    def main(self):
        """
        Forks a new prosess, letting the service run as
        a daemon.
        """
        os.sys.stdin=open('/dev/null','r')
        os.sys.stdout=open('/dev/null','w')
        os.sys.stderr=open('/dev/null','w')

        pid=os.fork()
        if pid > 0:
#            pidfile=open(PIDFILE, 'w')
#            pidfile.write(str(pid)+'\n')
#            pidfile.close()
            os.sys.exit()
        else:
            pass
            

if __name__=='__main__':
    controller=controller()
    controller.main()
