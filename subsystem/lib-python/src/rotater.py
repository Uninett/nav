#!/usr/bin/env python
# 
# Copyright (c) 2002-2003 Magnus Nordseth, Stian Søiland
# 
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#          Stian Søiland <stain@itea.ntnu.no>
# 
# License: MIT         
#

"""A rotating bar.
Shows a rotating bar while something is happening.
Log messages and status messages can be output as well,
with nice colors. Truly useful. (hehe)
"""

# KNOWN BUGS / TODO
# - The first line includes a duplicate bar/character
# - Not TERM aware - colors might not work overall
# - Not stdout-aware - should not write rotating
#   bar when piped to some other program/file

import sys
import time

ROTATION=r"/-\|"
DEL = '\010 \010'
GREEN = "\033[0;1;32m"
RED = "\033[0;1;31m"
YELLOW = "\033[0;1;33m"
DARK = "\033[0;34m"
RESET = "\033[0m"
OK = "%s[  %sOK  %s]%s" % (DARK, GREEN, DARK, RESET)
FAILED = "%s[%sFAILED%s]%s" % (DARK, RED, DARK, RESET)
WARN = "%s[ %sWARN %s]%s" % (DARK, YELLOW, DARK, RESET)
RESULTCODES = (OK, WARN, FAILED)



class RotaterPlugin:
    """This plugin class can be used by anyone who wants to rotate
    something. The 'only' catch is that every write to the screen
    must be done through either log(), status() or write(). 
    Call rotate() now and then from CPU intensive routines, the
    bar will rotate (unless it's already rotating at maxspeed).
    """
    def __init__(self, maxspeed=10, logStatus=True):
        """Initiates a rotator, maxspeed is maximum rotates pr. sec.
           If logStatus is true, old statuslines will be logged
           using log() when the status is changed.
        """
        self._rotation = -1 # current rotation state, -1==unstarted
        self._minwait = 1.0 / maxspeed # seconds to delay rotation
        self._lastRotated = 0
        self._status = ""
        self._logStatus = logStatus
    def rotate(self, noDelay=None):
        """Rotates the bar (if enough time has passed since last call)"""
        now = time.time()
        if (now - self._lastRotated) < self._minwait:
            return # skip rotation now
        self._lastRotated = now    
        self._erase()
        # modulo-rotate
        self._rotation = (self._rotation + 1) % len(ROTATION)
        self._drawRotate()
        sys.stdout.flush()
    def _drawRotate(self):    
        """Just draws the rotator"""
        sys.stdout.write(ROTATION[self._rotation])
    def _drawStatus(self):
        """Draws the statusline (if existing) and rotator. 
        Remember to erase first!"""
        if self._status:
            sys.stdout.write(self._status + " ")
        self._drawRotate()
    def _drawResult(self, result):
        if result in RESULTCODES:
            length = 8
        else:
            length = len(result)
        length += 1    
        sys.stdout.write(DEL*length) # go back to prev line
        sys.stdout.write(result+"\n")
    def _format(self, msgs):
        """Returns the arguments almost like when formatted by print"""
        msgs = [str(s) for s in msgs]   
        return ' '.join(msgs)
    def _erase(self, includeStatus=False):
        """Erases the rotator and optionally the statusline"""
        if self._rotation > -1:
            # We have started, erase previous rotate symbol
            sys.stdout.write(DEL)
        if includeStatus and self._status:
            # Delete the status message
            sys.stdout.write(DEL * (len(self._status)+1))
    def log(self, *msgs):        
        """Writes a logline independent of status line"""
        self._erase()
        self._log(self._format(msgs))
        self._drawStatus()
        sys.stdout.flush()
    def _log(self, msg):
        """Writes just the logline"""
        sys.stdout.write(msg + "\n")
        
    def status(self, *msg, **kwargs):
        """Sets status to the arguments given. If keyword arg 'result'
        is given, it will be the result of the previous command"""
        result = kwargs.get("result")    
        oldStatus = self._status
        self._erase(includeStatus=True)
        if oldStatus and self._logStatus:
            self._log(oldStatus)
            if result:
                self._drawResult(result)
        self._status = self._format(msg)
        if self._status:
            self._status += " " # add a space for the rotator
        self._drawStatus() 
        sys.stdout.flush()
    def reset(self, result=None):
        self._erase()
        sys.stdout.write("\n")
        if result:
            self._drawResult(result)
        sys.stdout.flush()
        sys.rotate = -1

def _test():
    import random
    foo = RotaterPlugin()
    messages = ['Calculation gravitation',
                'Getting nuclear blast ratio',
                'Initiating long range subspace scanners',
                'Extracting wormhole knowledge',
                'Sexifying',
                ]
    try:
        foo.status("Starting test")
        while 1:
            rand = random.random()
            if rand > 0.93:
                msg = random.choice(messages)
                if rand > 0.5:
                    # we're going status
                    result = random.choice(RESULTCODES)
                    foo.status(msg, result=result)
                else:
                    foo.status(msg)
            foo.rotate()
            time.sleep(random.random() / 10)
            if rand > 0.99:
                raise KeyboardInterrupt
    except KeyboardInterrupt:
        foo.status("Aborting", result=FAILED)
        foo.reset(result=OK)

if __name__ == '__main__':
    _test()

            
