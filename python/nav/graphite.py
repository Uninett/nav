# Copyright (C) 2013 UNINETT AS
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
"""Sending metrics to graphite.

This module implements various common API to send metrics to a
Graphite/Carbon backend. It currently only supports the UDP line protocol,
as it's the easiest to implement, and will also work without vodoo in
asynchronouse programs (i .e. such as ipdevpoll, which is implented using
Twisted).

"""
import socket

# with a 1500 byte MTU running on IPv4 this would be 1472, lets round it down
MAX_UDP_PAYLOAD = 1400


def send_metrics_to(metric_tuples, host, port=2003):
    """
    Sends a list of metric tuples to a carbon backend.

    :param metric_tuples: A list of metric tuples in the form
                          [(path, (timestamp, value)), ...]
    :param host: IP address of the carbon backend
    :param port: The carbon backend UDP port

    """
    carbon = socket.socket(_socktype_from_addr(host), socket.SOCK_DGRAM)
    carbon.connect((host, port))
    for packet in metrics_to_packets(metric_tuples):
        carbon.send(packet)


def _socktype_from_addr(addr):
    info = socket.getaddrinfo(addr, 0)
    socktype = info[0][0]
    return socktype


def metrics_to_packets(metric_tuples):
    """
    Converts a list of metric tuples to a series of Graphite/Carbon
    protocol packets ready to transmit over the wire (UDP) to a Carbon backend.

    :param metric_tuples: A list of metric tuples in the form
                          [(path, (timestamp, value)), ...]
    :return: A series of payload packets to send to a Carbon backend.

    """
    assert len(metric_tuples) > 0
    remainder = metric_tuples
    while remainder:
        packet, remainder = _consume_metrics_to_packet(remainder)
        if packet:
            yield packet


def _consume_metrics_to_packet(metric_tuples):
    remainder = []
    metrics = list(metric_tuples)
    packet = _metrics_to_packet(metrics)
    while len(packet) > MAX_UDP_PAYLOAD:
        remainder.insert(0, metrics.pop())
        packet = _metrics_to_packet(metrics)
    return packet, remainder


def _metrics_to_packet(metric_tuples):
    payload = ["%s %s %s" % (path, value, timestamp)
               for path, (timestamp, value) in metric_tuples]
    return "\n".join(payload)

