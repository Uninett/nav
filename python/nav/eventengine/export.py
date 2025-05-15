#
# Copyright (C) 2019 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Alert stream export functionality"""

import logging
import json
import subprocess

from django.core.serializers.json import DjangoJSONEncoder


from nav.web.api.v1.alert_serializers import AlertQueueSerializer

try:
    exporter
except NameError:
    """A singleton, normally instantiated by the event engine as it starts"""
    exporter = None

_logger = logging.getLogger(__name__)


class StreamExporter(object):
    """Exports a stream of alert objects over a pipe to a specific script"""

    def __init__(self, command):
        self.command = command
        self._process = None
        self.run()

    def run(self):
        """Runs the subprocess that will receive the alert stream on its STDIN"""
        self._process = subprocess.Popen(
            [self.command], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL
        )

    def is_ok(self):
        """Verifies that the subprocess is running, and attempts to restart it if
        it's dead.

        :returns: True if the subprocess is running, False if it wasn't running and
                  couldn't be restarted.

        """
        if self._process.poll() is not None:
            _logger.info(
                "restarting dead export script (retcode=%s) %r",
                self._process.returncode,
                self.command,
            )
            try:
                self.run()
            except Exception as error:  # noqa: BLE001
                _logger.error("Cannot restart dead export script: %s", error)
                return False

        return True

    def export(self, alert):
        """Serializes and exports an event or alert to the export script.

        :type alert: nav.models.event.AlertQueue

        """
        _logger.debug("exporting %r", alert)
        serializer = AlertQueueSerializer(alert)
        data = json.dumps(serializer.data, cls=DjangoJSONEncoder)
        self._send_string(data + "\n")

    def _send_string(self, string):
        if self.is_ok():
            self._process.stdin.write(
                string if not isinstance(string, str) else string.encode("utf-8")
            )
            self._process.stdin.flush()
