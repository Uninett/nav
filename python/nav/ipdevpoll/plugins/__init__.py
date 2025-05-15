#
# Copyright (C) 2008-2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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

import inspect
import logging

from nav.errors import GeneralException

from nav.ipdevpoll import Plugin

_logger = logging.getLogger(__name__)
plugin_registry = {}


class PluginImportError(GeneralException):
    """Failed to import plugin"""


def import_plugins():
    """Import all configured plugins into the plugin registry."""
    from nav.ipdevpoll.config import ipdevpoll_conf

    plugin_counter = 0
    for alias in ipdevpoll_conf.options('plugins'):
        import_plugin(ipdevpoll_conf, alias)
        plugin_counter += 1

    _logger.info(
        'Imported %d plugin classes, %d classes in plugin registry',
        plugin_counter,
        len(plugin_registry),
    )


def import_plugin(config, alias):
    """Attempts to import the plugin aliased to alias in config.

    If alias is set, but the config doesn't contain the full name of the
    plugin class, the module and class will be searched for in the
    nav.ipdevpoll.plugins package.

    """
    full_class_name = config.get('plugins', alias)
    if full_class_name:
        module_name = '.'.join(full_class_name.split('.')[:-1])
        class_name = full_class_name.split('.')[-1]
    else:
        module_name = 'nav.ipdevpoll.plugins.%s' % alias
        class_name = None

    _logger.debug('Importing plugin %s=%s', alias, full_class_name)
    try:
        module_ = __import__(module_name, globals(), locals(), [module_name])
        if class_name:
            class_ = getattr(module_, class_name)
        else:
            class_ = get_plugin_from_module(module_)
    except (ImportError, AttributeError) as error:
        _logger.exception("Failed to import plugin %s", full_class_name)
        raise PluginImportError(error)

    class_.alias = alias
    plugin_registry[alias] = class_
    class_.on_plugin_load()


def get_plugin_from_module(module_):
    """Tries to find a Plugin subclass in module_ and returns it"""

    def _predicate(thing):
        return (
            inspect.isclass(thing)
            and issubclass(thing, Plugin)
            and inspect.getmodule(thing) == module_
        )

    members = inspect.getmembers(module_, _predicate)
    if members:
        name, value = members[0]
        _logger.debug('found plugin class %s in %s', name, module_)
        return value
    else:
        raise AttributeError("no plugin class defined in module %r", module_)
