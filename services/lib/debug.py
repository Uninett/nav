"""
$Id: debug.py,v 1.1 2002/07/17 12:16:01 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/debug.py,v $
"""


loglevels={
    0:'Emergency',
    1:'Alert ',
    2:'Critical',
    3:'Error',
    4:'Warning',
    5:'Notice'
    6:'Info',
    7:'Debug'
}

def debug():
    if _debug._instance is None:
        _debug._instance=_debug()
    return _debug._instance

class _debug:
    _instance=None
    def __init__(self):
        pass

    def log(self, msg, level=6):
        print "%s %10s: %s" % ((time.strftime('%d %b %Y %H:%M:%S ', time.localtime()), loglevels[level], msg))
        
