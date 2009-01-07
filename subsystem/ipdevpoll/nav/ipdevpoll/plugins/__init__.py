"""ipdevpoll plugin handling.

This package contains plugins submodules as distributed with NAV.

"""
__author__ = "Morten Brekkevold (morten.brekkevold@uninett.no)"
__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPLv2"

import logging

logger = logging.getLogger('ipdevpoll.plugins')
plugin_registry = set()

def import_plugins():
    """Import all know plugin modules.

    Each module is responsible for registering its classes in the
    plugin registry, using the register function in this module.

    """
    global logger
    names = (
        'ipdevpoll.plugins.iftable',
        'ipdevpoll.plugins.typeoid',
        'ipdevpoll.plugins.dnsname',
        #'ipdevpoll.plugins.test',
        )
    for plug in names:
        logger.debug('Importing plugin module %s', plug)
        __import__(plug)
    logger.info('Imported %d plugin modules, '
                '%d classes in plugin registry',
                len(names), len(plugin_registry))

def register(plugin_class):
    """Register a class in the plugin registry."""
    plugin_registry.add(plugin_class)
    logger.debug("Registered class in plugin registry: %s.%s",
                 plugin_class.__module__, plugin_class.__name__)
    return plugin_class
