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

    # Pre sort all plugins
    plugin_registry = topological_sort(plugin_registry)

def register(plugin_class):
    """Register a class in the plugin registry."""

    plugin_name = '.'.join([plugin_class.__module__, plugin_class.__name__])

    if plugin_class in plugin_registry:
        logger.debug("Plugin already registered: %s", plugin_name)
    else:
        plugin_registry.append(plugin_class)
        logger.debug("Registered class in plugin registry: %s", plugin_name)

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

    vertices = _find_vertices(plugins)
    safe_plugins = _find_safe_plugins(vertices)

    while safe_plugins:
        plugin = safe_plugins.pop()
        sorted_plugins.append(plugin)

        for child,parents in vertices.items():
            _remove_plugin_from_parents(child, parents, plugin)
            _update_safe_plugins(child, parents, safe_plugins)
            _remove_empty_vertices(child, parents, vertices)

    if vertices:
        raise GeneralException('Found at least on cycle in graph')

    return sorted_plugins

def _find_vertices(plugins):
    vertices = {}
    name_map = _get_name_map(plugins)

    # Populate vertices: {child: [parent1, parent2, ...]}
    for plugin in plugins:
        vertices[plugin] = _get_dependencies(plugin, name_map)

    return vertices

def _find_safe_plugins(vertices):
    safe_plugins = set()

    for child,parents in vertices.items():
        _update_safe_plugins(child, parents, safe_plugins)
        _remove_empty_vertices(child, parents, vertices)

    return safe_plugins

def _get_name_map(plugins):
    name_map = lambda plugin: ('%s.%s' % (plugin.__module__, plugin.__name__), plugin)

    return dict(map(name_map, plugins ))

def _get_dependencies(plugin, name_map):
    if not hasattr(plugin, 'dependencies'):
        return []

    try:
        return [name_map[n] for n in plugin.dependencies]
    except KeyError:
        # We could try and auto import missing plugins, however this
        # complexity is probably more trouble than what it is worth.

        raise GeneralException('Dependency "%s" for %s is not met' %
            (n, plugin))

def _remove_plugin_from_parents(child, parents, plugin):
    if plugin in parents:
        parents.remove(plugin)

def _update_safe_plugins(child, parents, safe_plugins):
    if not parents:
        safe_plugins.add(child)

def _remove_empty_vertices(child, parents, vertices):
    if not parents:
        del vertices[child]
