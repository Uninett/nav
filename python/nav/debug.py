#
# Copyright (C) 2011 Uninett AS
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
"""This module provides some useful debugging tools for NAV developers"""

import logging
import pprint
from traceback import print_stack
from io import StringIO


def calltracer(function, logfunction=print):
    """Decorator to trace function calls.

    Decorate any function/method with calltracer to log tracebacks
    of each call to the function.

    :param logfunction: A function that accepts a string argument. The
                        default function will just print to stdout.

    """

    def _tracer(*args, **kwargs):
        logfunction(
            'TRACE: Call to %s, args=%s, kwargs=%s'
            % (repr(function), repr(args), repr(kwargs))
        )
        trace = StringIO()
        print_stack(file=trace)
        trace.seek(0)
        for line in trace.readlines():
            logfunction('STACK: ' + line.rstrip())
        return function(*args, **kwargs)

    if not logfunction:
        return function
    else:
        return _tracer


def log_stacktrace(logger, stacktrace):
    """Debug logs a stacktrace, including the global and local variables from
    each stack frame.

    :param logger: A logging.Logger instance.
    :param stacktrace: An output from the inspect.trace() function.

    """
    if not logger.isEnabledFor(logging.DEBUG):
        # don't waste time here if DEBUG logging isn't activated
        return

    dump = []
    for frame, filename, line_no, func, source, _ in stacktrace:
        dump.append("  File %r, line %s, in %s" % (filename, line_no, func))
        for line in source:
            dump.append("  %s" % line.rstrip())

        dump.append("(Globals)")
        globs = (
            (var, val) for var, val in frame.f_globals.items() if var != '__builtins__'
        )
        dump.extend(_dumpvars(globs))

        dump.append("(Locals)")
        dump.extend(_dumpvars(frame.f_locals.items()))
        dump.append("")

    logger.debug("Stack frame dump:\n%s", '\n'.join(dump))
    logger.debug("--- end of stack trace ---")


def _dumpvars(varitems):
    for var, val in varitems:
        try:
            yield "  %r: %s" % (var, pprint.pformat(val, indent=2))
        except Exception as err:  # noqa: BLE001
            yield "  %r: <<exception during formatting: %s>>" % (var, err)


def log_last_django_query(logger):
    """Debug logs the latest SQL query made by Django.

    Will only work if the DEBUG=True in the Django settings.

    :param logger: The logging.Logger object to use for logging.
    """
    from nav.models import manage as _manage  # noqa: F401 - import needed for debugging
    from django.db import connection

    if connection.queries:
        logger.debug("Last Django SQL query was: %s", connection.queries[-1]['sql'])
