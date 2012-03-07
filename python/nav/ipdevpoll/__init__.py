#
# Copyright (C) 2008-2012 UNINETT AS
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
from .log import ContextLogger, ContextFormatter

class Plugin(object):

    """Abstract class providing common functionality for all polling plugins.

    Do *NOT* create instances of the base class.

    """
    _logger = ContextLogger()

    def __init__(self, netbox, agent, containers, config=None):
        self.netbox = netbox
        self.agent = agent
        self.containers = containers
        self.config = config
        # touch _logger to initialize logging context right away
        # pylint: disable=W0104
        self._logger

    def __str__(self):
        return '%s(%s)' % (self.full_name(), repr(self.netbox.sysname))

    def __repr__(self):
        return '%s(%s)' % (self.full_name(), repr(self.netbox))

    def handle(self):
        """Handle plugin business, return a deferred."""
        raise NotImplementedError

    # this is an API, so netbox goes unused in the base class:
    # pylint: disable=W0613
    @classmethod
    def can_handle(cls, netbox):
        """Verifies whether this plugin can/wants to handle polling for this
        netbox instance at this time.

        The base implementation always returns True; plugins must override
        this method if they do not handle everything thrown at them at all
        times.

        :returns: A boolean value.
        """
        return True

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
