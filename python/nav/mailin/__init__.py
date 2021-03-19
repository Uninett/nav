# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""MailIn

E-Mail to NAV event/alert translator.

"""

import nav
import nav.event


def make_event(**kw):
    """Shortcut to make an event with mailin as source and eventEngine as
    target.

    Keyword arguments are the same as for nav.event.Event().

    """
    return nav.event.Event(source='mailin', target='eventEngine', **kw)


class Plugin(object):
    """Abstract base class for mailin plugin.

    Subclass this and override the init(), accept(),
    authorize() and process() methods.
    """

    def __init__(self, name, config, logger):
        self.name = name
        self.config = config
        self.logger = logger
        self.init()

    #
    # These methods are meant to be overriden.
    #

    def init(self):
        """Plugin specific initialization."""
        raise NotImplementedError

    def accept(self, msg):
        """Returns True if the plugin wants to process the message."""
        raise NotImplementedError

    def authorize(self, msg):
        """Returns True if the message is authorized by the plugin.
        (This method typically checks the From and Reveiced headers.)"""
        raise NotImplementedError

    def process(self, msg):
        """Process the message.
        Called if accept() and authorize() both return True.
        Returns True if the plugin posted one or more events.
        """
        raise NotImplementedError
