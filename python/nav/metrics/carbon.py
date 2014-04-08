#
# Copyright (C) 2013 UNINETT
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
"""
This module implements various common API to send metrics to a
Graphite/Carbon backend. It currently only supports the UDP line protocol,
as it's the easiest to implement, and will also work without vodoo in
asynchronous programs (i .e. such as ipdevpoll, which is implemented using
Twisted).
"""
import logging
import socket
from nav.metrics import CONFIG

_logger = logging.getLogger(__name__)

# Maximum payload to allow for a UDP packet containing metrics destined for
# Graphite. A value of 1472 should be ok to stay within the standard ethernet
# MTU of 1500 bytes using IPv4. Larger values will cause packet
# fragmentation, but should still work.
MAX_UDP_PAYLOAD = 1400


def send_metrics_to(metric_tuples, host, port=2003):
    """
    Sends a list of metric tuples to a carbon backend.

    :param metric_tuples: A list of metric tuples in the form
                          [(path, (timestamp, value)), ...]
    :param host: IP address of the carbon backend
    :param port: The carbon backend UDP port

    """
    # pylint: disable=W0601
    global carbon
    try:
        carbon
    except NameError:
        carbon = socket.socket(_socktype_from_addr(host), socket.SOCK_DGRAM)
        carbon.connect((host, port))

    _logger.debug("sending carbon metrics to [%s]:%s: %r",
                  host, port, metric_tuples)
    for packet in metrics_to_packets(metric_tuples):
        carbon.send(packet)


def send_metrics(metric_tuples):
    """Sends a list of metric tuples to the pre-configured carbon backend.

    :param metric_tuples: A list of metric tuples in the form
                          [(path, (timestamp, value)), ...]

    """
    host = CONFIG.get("carbon", "host")
    port = CONFIG.getint("carbon", "port")
    return send_metrics_to(metric_tuples, host, port)


def _socktype_from_addr(addr):
    info = socket.getaddrinfo(addr, 0)
    socktype = info[0][0]
    return socktype


def _metric_to_line(metric_tuple):
    path, (timestamp, value) = metric_tuple
    return str("%s %s %s\n" % (path, value, timestamp))


def metrics_to_packets(metric_tuples):
    """
    Converts a list of metric tuples to a series of Graphite/Carbon
    protocol packets ready to transmit over the wire (UDP) to a Carbon backend.

    :param metric_tuples: A list of metric tuples in the form
                          [(path, (timestamp, value)), ...]

    :return: A generator that yields a series of payload packets to send to a
             Carbon backend.

    """
    assert len(metric_tuples) > 0

    output = []
    size = 0
    for metric in metric_tuples:
        line = _metric_to_line(metric)
        if size + len(line) > MAX_UDP_PAYLOAD:
            packet = "".join(output)
            yield packet
            output = []
            size = 0

        output.append(line)
        size += len(line)

    if output:
        packet = "".join(output)
        yield packet