"""
$Id: debug.py,v 1.1 2003/03/26 16:01:43 magnun Exp $
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

def debug(*args, **kwargs):
    if _debug._instance is None:
        _debug._instance=_debug(*args,**kwargs)
    else:
        _debug._instance.debuglevel=kwargs.get('level',_debug._instance.debuglevel)
    return _debug._instance

class _debug:
    _instance=None
    def __init__(self, *args, **kwargs):
        level=kwargs.get('level',7)
        self.debuglevel=int(level)
        msg = "Setting debuglevel=%s" % level
        self.log(msg)

    def log(self, msg, level=5):
        if level <= self.debuglevel:
            (frame,file,line,func,_,_) = inspect.stack()[1]
            file = file and os.path.basename(file)
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            stack = "%s:%s:%s" % (file, func, line)
            # msg = "[%s %-25s %-8s] %s" % (now, stack, loglevels[level], msg)
            msg = "[%s] %s [%s] %s" % (now, stack, loglevels[level], msg)
            print msg
            #print "%s %-8s %s" % ((time.strftime('%Y-%m-%d %H:%M:%S ', time.localtime()), loglevels[level], msg.strip()))
            if not sys.stdout.isatty():
                sys.stdout.flush()
