# -*- coding: ISO8859-1 -*-
#
# Copyright 2002, 2005 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# $Id: checkermap.py,v 1.1 2003/06/19 12:51:14 magnun Exp $
# Authors: Magnus Nordseth <magnun@stud.ntnu.no>
#          Erik Gorset  <erikgors@stud.ntnu.no>
#
import os
import sys
import re
import debug
from debug import debug

checkers = {}
dirty = []  # store failed imports here
checkerdir = os.path.join(os.path.dirname(__file__), "checker")
if checkerdir not in sys.path:
    sys.path.append(checkerdir)
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

                
