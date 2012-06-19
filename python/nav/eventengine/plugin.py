#
# Copyright (C) 2012 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"event engine plugin handling"

class UnsupportedEvent(ValueError):
    pass

class EventHandler(object):
    "Base class for event handlers"
    handled_types = []

    @classmethod
    def can_handle(cls, event):
        """Verifies whether this handler can handle the specific event.

        :returns: The default implementation will return True for all events,
                  unless the class variable `handled_types` is a list of
                  accepted event type ids.

        """
        return (event.event_type_id in cls.handled_types
                if cls.handled_types else True)

    def __init__(self, event):
        if not self.can_handle(event):
            raise UnsupportedEvent("%s can't handle %s" % (
                    self.__class__.__name__, event.event_type_id))
        self.event = event

    def handle(self):
        "Handles the attached event"
        raise NotImplementedError
