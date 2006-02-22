# -*- coding: ISO8859-1 -*-
#
# Copyright 2003 Norwegian University of Science and Technology
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
# $Id: $
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#
"""
Module for writing debug messages.
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
    global debuglevel
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

