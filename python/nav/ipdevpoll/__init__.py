# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, 2009 UNINETT AS
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

import logging
from logging import Formatter

from nav.errors import GeneralException

class Plugin(object):

    """Abstract class providing common functionality for all polling plugins.

    Do *NOT* create instances of the base class.

    """

    def __init__(self, netbox, agent, containers, config=None):
        self.netbox = netbox
        self.agent = agent
        self.containers = containers
        self.config = config
        self.logger = get_instance_logger(self, "(%s)" % self.netbox.sysname)

    def __str__(self):
        return '%s(%s)' % (self.full_name(), repr(self.netbox.sysname))

    def __repr__(self):
        return '%s(%s)' % (self.full_name(), repr(self.netbox))

    def handle(self):
        """Handle plugin business, return a deferred."""
        raise NotImplemented

    @classmethod
    def can_handle(cls, netbox):
        """Verify whether this plugin can/wants to handle polling for this
        netbox instance at this time.

        Returns a boolean value.
        """
        raise NotImplemented

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



def get_class_logger(cls):
    """Return a logger instance for a given class object.

    The logger object is named after the fully qualified class name of
    the cls class.

    """
    full_class_name = "%s.%s" % (cls.__module__, cls.__name__)
    return logging.getLogger(full_class_name.lower())

def get_instance_logger(instance, instance_id=None):
    """Return a logger instance for a given instance object.

    The logger object is named after the fully qualified class name of
    the instance object + '.' + an instance identifier.

    If the instance_id parameter is omitted, str(instance) will be
    used as the identifier.

    """
    if not instance_id:
        instance_id = str(instance)
    cls = instance.__class__
    full_instance_name = "%s.%s.%s" % (cls.__module__,
                                       cls.__name__,
                                       instance_id)
    return logging.getLogger(full_instance_name.lower())

class ContextFormatter(Formatter):
    """A log formatter that will add context data if available in the record.

    Only recognizes the attributes 'job' and 'sysname' as context data.

    """
    def __init__(self):
        self._normal_fmt = "%(asctime)s [%(levelname)s %(name)s] %(message)s"
        self._context_fmt = ("%(asctime)s [%(levelname)s "
                             "%(name)s] [%(context)s] %(message)s")
        Formatter.__init__(self, self._normal_fmt)

    def format(self, record):
        """Overridden to choose format based on record contents."""
        context = [getattr(record, attr)
                   for attr in ('job', 'sysname')
                   if hasattr(record, attr)]
        if context:
            record.__dict__['context'] = ' '.join(context)
            self._fmt = self._context_fmt
        else:
            self._fmt = self._normal_fmt

        return Formatter.format(self, record)
