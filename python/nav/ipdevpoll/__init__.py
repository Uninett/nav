#
# Copyright (C) 2008-2011 UNINETT AS
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
"""NAV subsystem for IP device polling.

Packages:

  plugins -- polling plugin system

Modules:

  daemon  -- device polling daemon
  models  -- internal data models
  snmpoid -- snmpoid based poll run scheduling

"""
from .log import get_context_logger, get_class_logger
from .log import ContextLogger, ContextFormatter

class Plugin(object):

    """Abstract class providing common functionality for all polling plugins.

    Do *NOT* create instances of the base class.

    """

    def __init__(self, netbox, agent, containers, config=None, context=None):
        self.netbox = netbox
        self.agent = agent
        self.containers = containers
        self.config = config
        if not context:
            context = dict(sysname=self.netbox.sysname)
        self._logger = get_context_logger(self, **context)

    def __str__(self):
        return '%s(%s)' % (self.full_name(), repr(self.netbox.sysname))

    def __repr__(self):
        return '%s(%s)' % (self.full_name(), repr(self.netbox))

    def handle(self):
        """Handle plugin business, return a deferred."""
        raise NotImplementedError

    @classmethod
    def can_handle(cls, netbox):
        """Verify whether this plugin can/wants to handle polling for this
        netbox instance at this time.

        Returns a boolean value.
        """
        raise NotImplementedError

    @classmethod
    def on_plugin_load(cls):
        """Called as the plugin class is loaded in the plugin registry.

        Can be used to perform any kind of initialization task that
        doesn't fit into module-level initialization.

        """
        pass

    def name(self):
        """Return the class name of this instance."""
        return self.__class__.__name__

    def full_name(self):
        """Return the full module and class name of this instance."""
        return "%s.%s" % (self.__class__.__module__,
                          self.__class__.__name__)
