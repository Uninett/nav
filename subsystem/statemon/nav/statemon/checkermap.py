"""
$Id: checkermap.py,v 1.1 2003/06/19 12:51:14 magnun Exp $
This file is part of the NAV project.

Copyright (c) 2002 by NTNU, ITEA nettgruppen


Author: Magnus Nordseth <magnun@stud.ntnu.no>
	Erik Gorset	<erikgors@stud.ntnu.no>
"""
import os, re, debug
from debug import debug
checkers = {}
dirty = []  # store failed imports here
checkerdir = os.path.join(os.path.dirname(__file__), "checker")
if checkerdir not in os.sys.path:
    os.sys.path.append(checkerdir)
def register(key, module):
    if not key in checkers.keys():
        debug("Registering checker %s from module %s" % (key, module))
        checkers[key] = module

def get(checker):
    if checker in dirty:
        return
    if not checker in checkers.keys():
        parsedir()
    module = checkers.get(checker.lower(),'')
    if not module:
        return
    try:
        exec( "import "+ module)
    except Exception, e:
        debug("Failed to import %s, %s" % (module, str(e)))
        dirty.append(checker)
        return
    return eval(module+'.'+module)

def parsedir():
    """
    Parses the checkerdir for Handlers.
    
    """
    files=os.listdir(checkerdir)
    handlerpattern="Checker.py"
    for file in files:
        if file.endswith(handlerpattern):
            key = file[:-len(handlerpattern)].lower()
            handler = file[:-3]
            register(key, handler)

                
