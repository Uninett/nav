"""
$Id: debug.py,v 1.4 2003/01/02 22:01:26 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/debug.py,v $
"""

import time, sys
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
    def __init__(self,level=5):
        self.debuglevel=level

    def log(self, msg, level=5):
        if level <= self.debuglevel:
            print "%s %-8s %s" % ((time.strftime('%Y-%m-%d %H:%M:%S ', time.localtime()), loglevels[level], msg.strip()))
            if not sys.stdout.isatty():
                sys.stdout.flush()
