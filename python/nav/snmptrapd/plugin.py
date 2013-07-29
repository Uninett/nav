
import logging
from nav.errors import GeneralException

_LOGGER = logging.getLogger('nav.snmptrapd')


class ModuleLoadError(GeneralException):
    """Failed to load module"""
    pass

def load_handler_modules(modules):
    """
    Loads handlermodules
    :param modules plugin names as ['nav.snmptrapd.handlers.foo',
    'nav.snmptrapd.handlers.bar']
    """

    # Try to use __import__ to load every plugin under runtime and
    # return loaded modules in a list when done.
    #
    # This is usually done by the snmptrapd daemon in bin/ ;-)

    handlermodules = []
    for name in modules:
        name = name.strip()
        parts = name.split('.')
        parent = '.'.join(parts[:-1])
        try:
            mod = __import__(name, globals(), locals(), [parent])

            try:
                mod.initialize()
            except AttributeError:
                pass # Silently ignore if module has no initialize method

            handlermodules.append(mod)
        except Exception, why:
            _LOGGER.exception("Module %s did not compile - %s", name, why)
            raise ModuleLoadError, why

    return handlermodules