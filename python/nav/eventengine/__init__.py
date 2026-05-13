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

import threading
import time
from subprocess import PIPE, STDOUT, Popen


class EventEngineProcess:
    """Runs eventengine as a background subprocess with output capture.

    Use as a context manager.  Poll a condition to detect when the desired
    state has been reached, then exit the context to kill the process.
    """

    def __init__(self):
        self._process = None
        self._output_lines = []
        self._reader_thread = None

    def __enter__(self):
        self._process = Popen(["eventengine", "-f"], stdout=PIPE, stderr=STDOUT)
        self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
        self._reader_thread.start()
        return self

    def __exit__(self, *exc_info):
        self._process.kill()
        self._process.wait()
        self._reader_thread.join(timeout=5)
        output = self.get_output()
        print(output)

    def _read_output(self):
        for line in self._process.stdout:
            self._output_lines.append(line.decode("utf-8", errors="replace"))

    def get_output(self):
        return "".join(self._output_lines)

    def wait_for_condition(self, condition, timeout=30, interval=0.5):
        """Poll *condition()* until it returns True or *timeout* is reached."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            retcode = self._process.poll()
            if retcode is not None:
                raise AssertionError(
                    f"eventengine exited unexpectedly (code {retcode}):\n"
                    f"{self.get_output()}"
                )
            if condition():
                return True
            time.sleep(interval)
        return False


def get_eventengine_output(timeout=10):
    """Deprecated wrapper — prefer :class:`EventEngineProcess`."""
    with EventEngineProcess() as engine:
        time.sleep(timeout)
    return engine.get_output()
