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
The smsd dispatcher for Gammu.

This dispatcher takes care of all communication between smsd and Gammu. Gammu
is used to send SMS messages via a cell phone connected to the server with a
serial cable. See http://www.gammu.org/ for more information.
"""

__copyright__ = "Copyright 2006 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus@jodal.no)"
__id__ = "$Id$"

class dispatchgammu(object):
    "The smsd dispatcher for Gammu."
    def __init__(self):
        """Constructor."""
        pass # FIXME

    def formatsms(self, msgs):
        """
        Format a SMS from one or more messages.

        Pseudo code:
        If one message
            SMS = message
        If multiple messages
            SMS = as many msgs as possible + how many was ignored
        """

        sms = False # FIXME
        return sms # and what was sent and ignored

    def sendsms(self, sms):
        """
        Send SMS using Gammu
        """

        status = False # FIXME
        return status

