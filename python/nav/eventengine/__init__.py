#
# Copyright (C) 2012 Uninett AS
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
"""NAV eventengine"""

try:
    from subprocess32 import STDOUT, check_output, TimeoutExpired, CalledProcessError
except ImportError:
    from subprocess import STDOUT, check_output, TimeoutExpired, CalledProcessError


def get_eventengine_output(timeout=10):
    """
    Runs eventengine in foreground mode, kills it after timeout seconds and
    returns the combined stdout+stderr output from the process.
    Also asserts that pping shouldn't unexpectedly exit with a zero exitcode.
    """
    cmd = ["eventengine", "-f"]
    try:
        output = check_output(cmd, stderr=STDOUT, timeout=timeout)
    except TimeoutExpired as error:
        # this is the normal case, since we need to kill eventengine after the timeout
        print(error.output.decode("utf-8"))
        return error.output.decode("utf-8")
    except CalledProcessError as error:
        print(error.output.decode("utf-8"))
        raise
    else:
        print(output)
        assert False, "eventengine exited with non-zero status"
