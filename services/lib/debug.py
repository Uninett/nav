"""
$Id: debug.py,v 1.5 2003/01/03 19:19:55 magnun Exp $                                                                                                                              
This file is part of the NAV project.                                                                                             
                                                                                                                                 
Copyright (c) 2002 by NTNU, ITEA nettgruppen                                                                                      
Author: Magnus Nordseth <magnun@stud.ntnu.no>
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
