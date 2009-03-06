# -*- coding: ISO8859-1 -*-
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
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
# $Id$
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#

from nav.statemon.abstractChecker import AbstractChecker
from nav.event import Event


class DummyChecker(AbstractChecker):
    def __init__(self,*args):
        AbstractChecker.__init__(self,'dummy',*args)
    def execute(self):
        import random
        time.sleep(random.random()*10)
        return Event.UP,'OK'

def getRequiredArgs():
    """
    Returns a list of required arguments
    """
    requiredArgs = []
    return requiredArgs

