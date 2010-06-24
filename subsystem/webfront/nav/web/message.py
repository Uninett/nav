# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Message handling for NAV.
A message is stored in a users session and can be displayed to the user to give
confirmation, warnings or other types of messages.
"""

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
        if hasattr(request, '_req'):
            request = request._req
        self.session = request.session

    def __new__(cls, request=None):
        # We try to fetch a Messages object from this users session.
        # If it doesn't exist we make a new one.
        if hasattr(request, '_req'):
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
