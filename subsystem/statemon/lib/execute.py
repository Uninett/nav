import popen2
import select
import signal
import os
import time

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
                self.instance.tochild.close()
                self.instance.fromchild.close()
                # this is a bit ugly, but we need to let the os
                # actually kill the process.
                time.sleep(1)
                # do some cleanup
                popen2._cleanup()
                raise Timeout('Timeout while executing %s' % self.cmd)
            else:
                answer = r[0].read()
                self.instance.tochild.close()                
                self.instance.fromchild.close()
                # do some cleanup...
                popen2._cleanup()
                return answer
