"""
$Id: debug.py,v 1.2 2002/07/17 18:01:36 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/debug.py,v $
"""

import time
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

def debug():
    if _debug._instance is None:
        _debug._instance=_debug()
    return _debug._instance

class _debug:
    _instance=None
    def __init__(self,level=6):
        self.debuglevel=level

    def log(self, msg, level=6):
        if level <= self.debuglevel:
            print "%s %-8s %s" % ((time.strftime('%H:%M:%S ', time.localtime()), loglevels[level], msg.strip()))
        
