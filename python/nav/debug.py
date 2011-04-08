# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Norwegian University of Science and Technology
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
"""This module provides some useful debugging tools for NAV developers"""

from traceback import print_stack
from cStringIO import StringIO

try:
    from mod_python import apache
except ImportError:
    apache = None
    apache_log = None
else:
    apache_loglevel = apache.APLOG_WARNING
    def apache_log(s):
        """Log s to apaches error log"""
        apache.log_error(s, apache_loglevel)

def calltracer(function, logfunction=apache_log):
    """Decorator to trace function calls.

    Decorate any function/method with calltracer to log tracebacks
    of each call to the function.  The logfunction parameter
    specifices which log function to use.  The default logfunction
    logs to Apache's errorlog (if mod_python.apache is available),
    which makes this suitable for debugging the web modules of NAV.
    """
    def tracer(*args, **kwargs):
        logfunction('TRACE: Call to %s, args=%s, kwargs=%s' %
                    (repr(function), repr(args), repr(kwargs)))
        trace = StringIO()
        print_stack(file=trace)
        trace.seek(0)
        for line in trace.readlines():
            logfunction('STACK: ' + line.rstrip())
        return function(*args, **kwargs)

    if not logfunction:
        return function
    else:
        return tracer

