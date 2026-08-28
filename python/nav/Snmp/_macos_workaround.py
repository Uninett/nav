#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Workaround for pynetsnmp crashing on macOS.

pynetsnmp loads libcrypto with RTLD_GLOBAL at import time, which on macOS
conflicts with Python's own OpenSSL/LibreSSL and aborts the process with
"loading libcrypto in an unsafe way".

This module provides a context manager that intercepts ctypes.CDLL calls
and skips loading libcrypto.dylib, so pynetsnmp can be imported safely.
"""

import sys
from contextlib import contextmanager, nullcontext


@contextmanager
def _patched_libcrypto():
    import ctypes

    real_init = ctypes.CDLL.__init__

    def skip_libcrypto(self, name, *args, **kwargs):
        if name and str(name).endswith('libcrypto.dylib'):
            return real_init(self, None, *args, **kwargs)
        return real_init(self, name, *args, **kwargs)

    ctypes.CDLL.__init__ = skip_libcrypto
    try:
        yield
    finally:
        ctypes.CDLL.__init__ = real_init


safe_libcrypto_import = _patched_libcrypto if sys.platform == "darwin" else nullcontext
