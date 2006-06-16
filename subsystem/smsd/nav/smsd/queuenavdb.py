#! /usr/bin/env python
# -*- coding: ISO8859-1 -*-
#
# Copyright 2006 UNINETT AS
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

"""
The smsd queue for the NAV database.

This smsd queue takes care of all communication between smsd and the NAV
database. Replacing the NAV database with some other queue/input should be
possible by implementing the interface seen in this class.
"""

__copyright__ = "Copyright 2006 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus@jodal.no)"
__id__ = "$Id$"

import nav.db
dbconn = nav.db.getConnection('navprofile')
from nav.db.navprofiles import Smsq

class queuenavdb(object):
    "The smsd queue for the NAV database."
    def __init__(self):
        """Constructor."""
        pass # FIXME

    def cancel(self):
        """Mark all unsent messages as ignored."""
        pass # FIXME

    def getusers(self, status):
        """Get users which has messages with status (normally unsent)."""
        pass # FIXME

    def getusermsgs(self, user, status):
        """Get the users messages which has status (normally unsent)."""
        pass # FIXME

