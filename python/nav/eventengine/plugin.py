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

from __future__ import absolute_import
import os

class UnsupportedEvent(ValueError):
    "Event of unsupported type was passed to a handler"
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

    @classmethod
    def load_and_find_subclasses(cls, package_names=None):
        """Loads all modules from the listed packages and subsequently returns
        list of all defined subclasses of EventHandler.

        """
        if not package_names:
            from . import plugins
            package_names = [plugins.__name__]

        for name in package_names:
            _load_all_modules_in_package(name)
        # hey mr. pylint, every class has __subclasses__, you idiot!
        # pylint: disable=E1101
        return cls.__subclasses__()


def _load_all_modules_in_package(package_name):
    modnames = ('%s.%s' % (package_name, mod)
                for mod in _find_package_modules(package_name))
    for name in modnames:
        __import__(name, fromlist=['*'])

def _find_package_modules(package_name):
    extensions = ('.py', '.pyc')
    package = __import__(package_name, fromlist=['*'])
    directory = os.path.dirname(package.__file__)
    files = (os.path.splitext(f) for f in os.listdir(directory)
             if not f.startswith('.') and not f.startswith('_'))
    modnames = set(name for name, ext in files if ext in extensions)
    return list(modnames)
