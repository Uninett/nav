#
# Copyright (C) 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
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
import event
from nav.graphite import metric_prefix_for_device, send_metrics


def update(netboxid, sysname, timestamp, status, responsetime, serviceid=None,
           handler=""):
    """Sends metric updates to graphite.

    :param netboxid: Netboxid. Not actually used, but preserved for
                     compatibility with old API.
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
    prefix = metric_prefix_for_device(sysname)
    if serviceid:
        prefix += '.services.%s_%s' % (handler, serviceid)
        status_name = '.availability'
        response_name = '.responseTime'
    else:
        prefix += '.ping'
        status_name = '.packetLoss'
        response_name = '.roundTripTime'

    if timestamp is None or timestamp == 'N':
        timestamp = time.time()

    metrics = [
        (prefix + status_name,
         (timestamp, 0 if status == event.Event.UP else 1)),
        (prefix + response_name, (timestamp, responsetime))
    ]
    send_metrics(metrics)
