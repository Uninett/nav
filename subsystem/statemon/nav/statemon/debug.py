"""
$Id: debug.py,v 1.2 2003/06/19 12:50:34 magnun Exp $
This file is part of the NAV project.

Copyright (c) 2002 by NTNU, ITEA nettgruppen
Author: Magnus Nordseth <magnun@stud.ntnu.no>
"""

import time
import sys
import inspect
import os.path

loglevels={
    0:'Emergency',
    1:'Alert ',
    2:'Critical',
    3:'Error',
    4:'Warning',
    5:'Notice',
    6:'Info',
    7:'Debug'
}

debuglevel = 5
def setDebugLevel(level):
    debuglevel = level

def debug(msg, level=5):
    if level <= debuglevel:
        (frame,file,line,func,_,_) = inspect.stack()[1]
        file = file and os.path.basename(file)
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        stack = "%s:%s:%s" % (file, func, line)
        # msg = "[%s %-25s %-8s] %s" % (now, stack, loglevels[level], msg)
        msg = "[%s] %s [%s] %s" % (now, stack, loglevels[level], msg)
        print msg
        if not sys.stdout.isatty():
            sys.stdout.flush()

