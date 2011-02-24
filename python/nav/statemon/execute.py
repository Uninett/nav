import popen2
import select
import signal
import os
from nav.daemon import safesleep as sleep

class Timeout(Exception):
    pass

class Executer:
    def __init__(self, cmd, timeout=0):
        self.cmd = cmd
        self.instance = popen2.Popen4(cmd)
        self.timeout = timeout
    def read(self):
        if not self.timeout:
            return self.instance.fromchild.read()
        else:
            r, w, e = select.select([self.instance.fromchild], [], [], self.timeout)
            if not r:
                # Things timed out. Kill the child
                os.kill(self.instance.pid, signal.SIGTERM)
                sleep(1)
                try:
                    pid, sts = os.waitpid(self.instance.pid, os.WNOHANG)
                    os.kill(self.instance.pid, 9)
                    print "Killed with -9, %s" % self.cmd
                except Exception, e:
                    print e
                os.close(self.instance.tochild.fileno())
                os.close(self.instance.fromchild.fileno())
                # this is a bit ugly, but we need to let the os
                # actually kill the process.
                
                # do some cleanup
                popen2._cleanup()
                raise Timeout('Timeout while executing %s' % self.cmd)
            else:
                answer = r[0].read()
                os.close(self.instance.tochild.fileno())
                os.close(self.instance.fromchild.fileno())
                # do some cleanup...
                popen2._cleanup()
                return answer
