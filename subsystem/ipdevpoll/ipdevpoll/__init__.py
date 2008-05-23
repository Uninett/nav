"""
NAV subsystem for IP device polling.
"""
__author__ = "Morten Brekkevold (morten.brekkevold@uninett.no)"
__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPLv2"

import logging
from nav.errors import GeneralException

class Plugin(object):
    """
    Base Plugin class to provide common useful functions for all
    polling plugins.  Do *NOT* create instances of the base class.
    """

    def __init__(self, netbox):
        self.netbox = netbox
        self.logger = get_instance_logger(self, "[%s]" % self.netbox.sysname)

    def __str__(self):
        return '%s(%s)' % (self.full_name(), repr(self.netbox.sysname))

    def __repr__(self):
        return '%s(%s)' % (self.full_name(), repr(self.netbox))

    def handle(self):
        """Handle plugin business, return a deferred"""
        raise NotImplemented

    @classmethod
    def can_handle(cls, netbox):
        """
        Returns a true value if this plugin class can/wants to handle
        polling for this netbox instance at this time.
        """
        raise NotImplemented

    def order(self, queue):
        """
        Offer a chance for this plugin to manipulate the order of the
        plugin calling queue prior to the handle method being called.
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
    """
    Get a logger with a name corresponding to the fully qualified
    class name of the class specified in the cls parameter.
    """
    full_class_name = "%s.%s" % (cls.__module__, cls.__name__)
    return logging.getLogger(full_class_name)

def get_instance_logger(instance, instance_id=None):
    """
    Get a logger with a name corresponding to the fully qualified
    class name and instance identifier of the instance in the instance
    parameter.

    If an instanceId parameter is specified, this string will be
    appended to the fully qualified class name (with a separating dot)
    of the instance to name the logger.  If omitted, str(instance) is
    used as an instance identifier.
    """
    if not instance_id:
        instance_id = str(instance)
    cls = instance.__class__
    full_instance_name = "%s.%s.%s" % (cls.__module__,
                                       cls.__name__,
                                       instance_id)
    return logging.getLogger(full_instance_name)
