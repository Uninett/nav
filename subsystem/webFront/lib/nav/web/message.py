# -*- coding: utf-8 -*-
#
# Copyright 2008 UNINETT AS
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
# Authors: Magnus Motzfeldt Eide <magnus.eide@uninett.no>
#

"""
Message handling for NAV.
A message is stored in a users session and can be displayed to the user to give
confirmation, warnings or other types of messages.
"""

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Magnus Motzfeldt Eide (magnus.eide@uninett.no)"
__id__ = "$Id$"

from copy import copy
from django.core.handlers.modpython import ModPythonRequest

from nav.web.state import setupSession, setSessionCookie, getSessionCookie, \
    deleteSessionCookie, Session

def new_message(request, message, type):
    """Convenience method for fetching Messages object and adding a new message
    to it.

    Automatically calls save, and should therefore only be used when there's
    only need for one message.
    """
    messages = Messages(request)
    messages.append({'message': message, 'type': type})
    messages.save()

class Messages(list):
    """List object that stores messsages for the user accross page views.
    Uses sessions.
    """
    SUCCESS = 'success'
    NOTICE = 'notice'
    WARNING = 'warning'
    ERROR = 'error'

    session = None

    def __init__(self, request=None):
        if isinstance(request, ModPythonRequest):
            request = request._req
        self.session = request.session

    def __new__(cls, request=None):
        # We try to fetch a Messages object from this users session.
        # If it doesn't exist we make a new one.
        if isinstance(request, ModPythonRequest):
            request = request._req
        setupSession(request)
        messages = request.session.get('messages', None)

        if not messages or not isinstance(messages, Messages):
            return list.__new__(cls)
        else:
            return messsages

    def save(self):
        """Save this Messages object to this users session.
        """
        messages = self.session.get('messages', [])
        messages.extend(self)
        self.session['messages'] = messages
        self.session.save()

    def get_and_delete(self):
        """Copies messages from this users session and purges the originals.
        """
        messages = copy(self.session.get('messages', None))
        self.session['messages'] = []
        self.session.save()
        return messages
