"""ipdevpoll plugin handling.

This package contains plugins submodules as distributed with NAV.

"""
__author__ = "Morten Brekkevold (morten.brekkevold@uninett.no)"
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

    plugin_registry = topological_sort(plugin_registry)

def register(plugin_class):
    """Register a class in the plugin registry."""
    plugin_registry.append(plugin_class)
    logger.debug("Registered class in plugin registry: %s.%s",
                 plugin_class.__module__, plugin_class.__name__)
    return plugin_class

def topological_sort(plugins):
    '''Sorts an itterable of plugins sorting them in topological order based on
       dependencies.

       Dependencies are retrived from the attribute dependencies on the plugins
       and should be in the form: ['nav.ipdevpoll.plugins.iftable.Interfaces', ...]

       Function raises errors on unmet dependencies and cycles in the
       dependency graph.

       Returns a sorted list of plugins.

       See: http://en.wikipedia.org/wiki/Topological_sort
    '''

    sorted_plugins = []
    all_plugins = set(plugins)
    vertices = {}
    name_map = {}

    for plugin in all_plugins:
        name_map['%s.%s' % (plugin.__module__, plugin.__name__)] = plugin

    # Populate vertices: {child: [parent1, parent2, ...]}
    for plugin in all_plugins:
        if hasattr(plugin, 'dependencies') and plugin.dependencies:
            try:
                vertices[plugin] = [name_map[n] for n in plugin.dependencies]
            except KeyError:
                raise GeneralException('Dependency "%s" for %s is not met' %
                    (n, plugin))

    # Plugins without any dependencies
    safe_plugins = all_plugins.difference(set(vertices.keys()))

    while safe_plugins:
        # Remove one of the plugins without any dependencies
        plugin = safe_plugins.pop()

        # Add it to the sorted list and remove it from the all_plugins set
        sorted_plugins.append(plugin)
        all_plugins.remove(plugin)

        for k,i in vertices.items():
            # Delete any vertices with the plugin in question
            if plugin in i:
                i.remove(plugin)
            if not i:
                del vertices[k]

            # Update list of safe_plugins based on new vertices data
            safe_plugins = safe_plugins.union(all_plugins.difference(set(vertices.keys())))

    if vertices:
        raise GeneralException('Found at least on cycle in graph')
    else:
        return sorted_plugins
