#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Helper for testing behaviour that only manifests outside a UTF-8 locale.

Encoding regressions like #4132 are only observable when the interpreter's
preferred encoding is not UTF-8, and that cannot be changed once the process has
started. Tests therefore hand a snippet to a child interpreter whose locale is
forced to plain ASCII.

Note that the child's command line is itself decoded using the ASCII locale, so
snippets must be pure ASCII. Build any non-ASCII expectation inside the snippet,
e.g. with ``chr(0x2014)`` rather than a literal em dash.
"""

import os
import subprocess
import sys

import pytest

_COULD_NOT_FORCE_ASCII = 99

# Prepended to every snippet, so a UTF-8-insisting interpreter bails out before
# the snippet's own imports run.
_SKIP_UNLESS_ASCII = """
import locale
import sys

if "utf" in locale.getpreferredencoding(False).lower().replace("-", ""):
    sys.exit({sentinel})
""".format(sentinel=_COULD_NOT_FORCE_ASCII)


def assert_runs_in_ascii_locale(script, **extra_env):
    """Run script in a child interpreter forced to a non-UTF-8 locale.

    Skips the calling test if the interpreter cannot be talked out of UTF-8, and
    fails it if the script exits non-zero, reporting the child's stderr.

    Any keyword arguments are added to the child's environment.
    """
    result = _run_in_ascii_locale(_SKIP_UNLESS_ASCII + script, extra_env)
    if result.returncode == _COULD_NOT_FORCE_ASCII:
        pytest.skip("interpreter could not be forced to a non-UTF-8 locale")
    assert result.returncode == 0, result.stderr


def _run_in_ascii_locale(script, extra_env):
    env = {
        **os.environ,
        "LC_ALL": "C",
        "LANG": "C",
        "PYTHONUTF8": "0",
        "PYTHONCOERCECLOCALE": "0",
        **extra_env,
    }
    return subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
