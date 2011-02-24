#
# Copyright (C) 2011 UNINETT AS
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
"""Encoding fix-ups for content served directly through mod_python APIs"""
from functools import wraps

PREFERRED_ENCODING = 'utf-8'

def encoded_output(func):
    """Decorates a mod_python handler to ensure any writes of unicode objects
    to req.write() are encoded properly to UTF-8.

    """
    def _handler(req, *args, **kwargs):
        req.write = encoded_request_writer(req.write)
        return func(req, *args, **kwargs)
    return wraps(func)(_handler)

def encoded_request_writer(func):
    """Decorates a mod_python.Request object's write method to ensure that any
    unicode objects submitted to the function are enocded as UTF-8.

    """
    def _write(string, **kwargs):
        if isinstance(string, unicode):
            string = string.encode(PREFERRED_ENCODING)
        return func(string, **kwargs)
    return wraps(func)(_write)
