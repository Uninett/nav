#
# Copyright (C) 2008-2012 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Logging utilities for ipdevpoll"""

import logging
from logging import Formatter
import inspect
from itertools import islice


class ContextFormatter(Formatter):
    """A log formatter that will add context data if available in the record.

    Only recognizes the attributes 'job' and 'sysname' as context data.

    """

    prefix = 'nav.ipdevpoll.'

    def __init__(self, pidlog=False):
        pidlog = "[%(process)s] " if pidlog else ""
        self._normal_fmt = (
            "%(asctime)s " + pidlog + "[%(levelname)s %(name)s] %(message)s"
        )
        self._context_fmt = (
            "%(asctime)s " + pidlog + "[%(levelname)s "
            "%(name)s] [%(context)s] %(message)s"
        )
        Formatter.__init__(self, self._normal_fmt)

    def format(self, record):
        """Overridden to choose format based on record contents."""
        self._set_context(record)
        record.name = record.name.removeprefix(self.prefix)
        return Formatter.format(self, record)

    def _set_context(self, record):
        context = [
            getattr(record, attr)
            for attr in ('job', 'sysname')
            if hasattr(record, attr)
        ]
        if context:
            record.__dict__['context'] = ' '.join(context)
            self._set_format(self._context_fmt)
        else:
            self._set_format(self._normal_fmt)

    def _set_format(self, fmt):
        self._fmt = fmt
        self._style._fmt = fmt


class ContextLogger(object):
    """Descriptor for getting an appropriate logger instance.

    A class that needs logging can use this descriptor to automatically get a
    logger with the correct name and context.  Example::

      class Foo(object):
          _logger = ContextLogger()

          def do_bar(self):
              self._logger.debug("now doing bar")

    The _logger attribute will be either a logging.Logger or
    logging.LoggerAdapter, depending on whether a logging context can be
    found.  The first time _logger is accessed, it establishes the context
    either via direct lookup on the owning instance, or via stack frame
    inspection.  If the current instance hasn't already established a logging
    context, but the calling client object has one, this context will be
    copied permanently to this instance.

    """

    log_attr = '_logger_object'

    def __init__(self, suffix=None, context_vars=None):
        if suffix:
            self.log_attr = "%s_%s" % (self.log_attr, suffix)

        self.suffix = suffix
        self.context_vars = context_vars

    def __get__(self, obj, owner=None):
        target = owner if obj is None else obj
        if hasattr(target, self.log_attr):
            return getattr(target, self.log_attr)

        logger = logging.getLogger(self._logger_name(owner))
        if target is obj:
            if self.context_vars:
                extra = dict((k, getattr(target, k, None)) for k in self.context_vars)
            elif hasattr(target, '_log_context'):
                extra = getattr(target, '_log_context')
            else:
                extra = _context_search(inspect.currentframe())

            if extra:
                logger = logging.LoggerAdapter(logger, extra)

        setattr(target, self.log_attr, logger)
        return logger

    def _logger_name(self, klass):
        if klass.__module__ != '__main__':
            name = "%s.%s" % (klass.__module__, klass.__name__)
        else:
            name = klass.__name__.lower()
        if self.suffix:
            name = name + '-' + self.suffix
        return name.lower()

    def __set__(self, obj, value):
        raise AttributeError("cannot reassign a %s attribute" % self.__class__.__name__)

    def __delete__(self, obj):
        raise AttributeError("cannot delete a %s attribute" % self.__class__.__name__)


#
# Utility functions for inspecting the call stack for logging contexts
#


def _context_search(frame, maxdepth=10):
    """Attempts to extract a logging context from the current stack"""
    frames = islice(_stack_iter(frame), maxdepth)
    return _first_true(_get_context_from_frame(f) for f in frames)


def _stack_iter(frame):
    "Iterates backwards through stack frames, starting with the one below frame"
    try:
        while frame.f_back:
            frame = frame.f_back
            yield frame
    finally:
        del frame


def _first_true(sequence):
    """Returns the first element from sequence that evaluates to a true value,
    or None if no such element was found.

    """
    for elem in sequence:
        if elem:
            return elem


def _get_context_from_frame(frame):
    "Returns a logging context from a stack frame, if found"
    obj = frame.f_locals.get('self', None)
    if obj is None:
        return
    if hasattr(obj, '_log_context'):
        return getattr(obj, '_log_context')
    elif hasattr(obj, '_logger'):
        logger = getattr(obj, '_logger')
        if hasattr(logger, 'extra'):
            return logger.extra
