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
"""ipdevpoll plugin handling.

This package contains plugins submodules as distributed with NAV.

"""

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
