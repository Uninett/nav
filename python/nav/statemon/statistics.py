#
# Copyright (C) 2013 Uninett AS
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
"""Module for keeping status/roundtrip time/response time statistics.

These used to be handled by rrdtool, but has completely moved to Graphite.
The only public API of this module used to be the update() function,
whose call signature has been kept to remain compatible with the rest of
the statemon subsystem.

"""

import time

from nav.metrics.carbon import send_metrics
from nav.metrics.templates import (
    metric_path_for_packet_loss,
    metric_path_for_roundtrip_time,
    metric_path_for_service_availability,
    metric_path_for_service_response_time,
)

from . import event


def update(sysname, timestamp, status, responsetime, serviceid=None, handler=""):
    """Sends metric updates to graphite.

    :param sysname: Sysname of the device in question.
    :param timestamp: Timestamp of the measurements. If None or 'N', the
                    current time will be used.
    :param status: Either Event.UP or Event.DOWN
    :param responsetime: Round-trip or response time of device/service.
    :param serviceid: Service id (db primary key) in case we're updating a
                      service handler.
    :param handler: The type of service handler in case we're updating a
                    service handler.

    """
    if serviceid:
        status_name = metric_path_for_service_availability(sysname, handler, serviceid)
        response_name = metric_path_for_service_response_time(
            sysname, handler, serviceid
        )
    else:
        status_name = metric_path_for_packet_loss(sysname)
        response_name = metric_path_for_roundtrip_time(sysname)

    if timestamp is None or timestamp == 'N':
        timestamp = time.time()

    metrics = [
        (status_name, (timestamp, 0 if status == event.Event.UP else 1)),
        (response_name, (timestamp, responsetime)),
    ]
    send_metrics(metrics)
