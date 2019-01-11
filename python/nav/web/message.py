#
# Copyright (C) 2008, 2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Message handling for NAV.

A message is stored in a user's session and can be displayed to the
user to give confirmation, warnings or other types of messages.

This was originally written to work with NAV sessions under mod_python,
before we supported a Django version with its on Message framework. Most
usage of this module can be replaced with Django's Message framework instead.

"""

from copy import copy


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
    NOTICE = 'secondary'
    WARNING = 'warning'
    ERROR = 'alert'

    session = None

    def __init__(self, request=None):
        self.session = request.session

    def __new__(cls, request=None):
        # We try to fetch a Messages object from this users session.
        # If it doesn't exist we make a new one.
        messages = request.session.get('messages', None)

        if not messages or not isinstance(messages, Messages):
            return list.__new__(cls)
        else:
            return messages

    def save(self):
        """Save this Messages object to this users session.
        """
        messages = self.session.get('messages', [])
        messages.extend(self)
        self.session['messages'] = messages

    def get_and_delete(self):
        """Copies messages from this user's session and purges the originals.
        """
        messages = copy(self.session.get('messages', None))
        if messages:
            self.session['messages'] = []
        return messages
