"""ipdevpoll plugin handling.

This package contains plugins submodules as distributed with NAV.

"""
__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPLv2"

import logging

from nav.errors import GeneralException

logger = logging.getLogger('ipdevpoll.plugins')
plugin_registry = [] # We don't use a set as ordering will matter

def import_plugins():
    """Import all know plugin modules.

    Each module is responsible for registering its classes in the
    plugin registry, using the register function in this module.

    """
    global plugin_registry

    names = (
        'nav.ipdevpoll.plugins.iftable',
        'nav.ipdevpoll.plugins.typeoid',
        'nav.ipdevpoll.plugins.dnsname',
        #'nav.ipdevpoll.plugins.test',
        )
    for plug in names:
        logger.debug('Importing plugin module %s', plug)
        __import__(plug)

    logger.info('Imported %d plugin modules, '
                '%d classes in plugin registry',
                len(names), len(plugin_registry))

def register(plugin_class):
    """Register a class in the plugin registry."""

    plugin_name = '.'.join([plugin_class.__module__, plugin_class.__name__])

    if plugin_class in plugin_registry:
        logger.debug("Plugin already registered: %s", plugin_name)
    else:
        plugin_registry.append(plugin_class)
        logger.debug("Registered class in plugin registry: %s", plugin_name)

    return plugin_class
