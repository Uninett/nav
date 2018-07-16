#
# Copyright 2013 (C) Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Snmptrapd plugin helpers"""

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
        except Exception as why:
            _LOGGER.exception("Module %s did not compile - %s", name, why)
            raise ModuleLoadError(why)

    return handlermodules
