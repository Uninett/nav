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

def register(key, module):
    if not key in checkers.keys():
        debug("Registering checker %s from module %s" % (key, module))
        checkers[key] = module

def get(checker):
    if not checker in checkers.keys():
        parsedir()
    module = checkers.get(checker,'')
    if not module:
        return
    exec( "import "+ module)
    return eval(module+'.'+module)

def parsedir():
    """
    Parses the dir lib/handler for Handlers.
    
    """
    files=os.listdir("./lib/checker/")
    handlerpattern="Checker.py"
    for file in files:
        if len(file) > len(handlerpattern) and file[len(file)-len(handlerpattern):]==handlerpattern:
            key = file[:-len(handlerpattern)].lower()
            handler = file[:-3]
            register(key, handler)

                
