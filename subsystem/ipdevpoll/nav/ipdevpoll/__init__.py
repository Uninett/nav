"""NAV subsystem for IP device polling.

Packages:

  plugins -- polling plugin system

Modules:

  daemon  -- device polling daemon
  models  -- internal data models
  snmpoid -- snmpoid based poll run scheduling

"""
__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPLv2"

import logging

from nav.errors import GeneralException

class Plugin(object):

    """Abstract class providing common functionality for all polling plugins.

    Do *NOT* create instances of the base class.

    """

    def __init__(self, netbox):
        self.netbox = netbox
        self.logger = get_instance_logger(self, "[%s]" % self.netbox.sysname)

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

    def order(self, queue):
        """Manipulate this plugin's order on the queue.

        The RunHandler may offer a plugin a chance to manipulate the
        list of plugin instances to run, by calling this method with
        the plugin list as its argument.

        When a plugin knows it needs to be run before or after a
        specific other plugin, it can check for that plugin's presence
        in the queue list, and if found, alter its own position in the
        list accordingly.

        """
        # By default do nothing here
        pass

    def name(self):
        """Return the class name of this instance."""
        return self.__class__.__name__

    def full_name(self):
        """Return the full module and class name of this instance."""
        return "%s.%s" % (self.__class__.__module__,
                          self.__class__.__name__)


class FatalPluginError(GeneralException):
    """Fatal plugin error"""
    pass


def get_class_logger(cls):
    """Return a logger instance for a given class object.

    The logger object is named after the fully qualified class name of
    the cls class.

    """
    full_class_name = "%s.%s" % (cls.__module__, cls.__name__)
    return logging.getLogger(full_class_name)

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
    return logging.getLogger(full_instance_name)
