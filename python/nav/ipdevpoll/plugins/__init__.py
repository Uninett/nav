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

logger = logging.getLogger(__name__)
plugin_registry = {}

class PluginImportError(GeneralException):
    """Failed to import plugin"""

def import_plugins():
    """Import all configured plugins into the plugin registry."""
    from nav.ipdevpoll.config import ipdevpoll_conf
    global plugin_registry

    plugin_counter = 0
    for alias in ipdevpoll_conf.options('plugins'):
        import_plugin(ipdevpoll_conf, alias)
        plugin_counter += 1

    logger.info('Imported %d plugin classes, '
                '%d classes in plugin registry',
                plugin_counter, len(plugin_registry))


def import_plugin(config, alias):
    global plugin_registry
    full_class_name = config.get('plugins', alias)
    module_name = '.'.join(full_class_name.split('.')[:-1])
    class_name = full_class_name.split('.')[-1]

    logger.debug('Importing plugin %s=%s', alias, full_class_name)
    try:
        module_ = __import__(module_name, globals(), locals(),
                             [module_name])
        class_ = getattr(module_, class_name)
    except (ImportError, AttributeError), error:
        logger.exception("Failed to import plugin %s", full_class_name)
        raise PluginImportError(error)

    plugin_registry[alias] = class_
    class_.on_plugin_load()
