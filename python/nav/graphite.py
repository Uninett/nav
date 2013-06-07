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
asynchronous programs (i .e. such as ipdevpoll, which is implented using
Twisted).

"""
import socket
from nav.config import NAVConfigParser

###################
# INITIALIZATIONS #
###################

# Maximum payload to allow for a UDP packet containing metrics destined for
# Graphite. A value of 1472 should be ok to stay within the standard ethernet
# MTU of 1500 bytes using IPv4. Larger values will cause packet
# fragmentation, but should still work.
MAX_UDP_PAYLOAD = 1400


class GraphiteConfigParser(NAVConfigParser):
    """Parser for NAV's graphite related configuration"""
    DEFAULT_CONFIG_FILES = ['graphite.conf']
    DEFAULT_CONFIG = """
[carbon]
host = 127.0.0.1
port = 2003
"""

CONFIG = GraphiteConfigParser()
CONFIG.read_all()

#######
# API #
#######


def send_metrics(metric_tuples):
    """Sends a list of metric tuples to the pre-configured carbon backend.

    :param metric_tuples: A list of metric tuples in the form
                          [(path, (timestamp, value)), ...]

    """
    host = CONFIG.get("carbon", "host")
    port = CONFIG.getint("carbon", "port")
    return send_metrics_to(metric_tuples, host, port)


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


def _metric_to_line(metric_tuple):
    path, (timestamp, value) = metric_tuple
    return str("%s %s %s\n" % (path, value, timestamp))


def escape_metric_name(string):
    """Escapes any character of string that may not be used in graphite metric
    names, by replacing them with underscores.

    """
    for char in "./ ":
        string = string.replace(char, "_")
    return string


#########################
# metric path templates #
#########################
# pylint: disable=C0111


def metric_path_for_interface(sysname, ifname, counter):
    tmpl = "{ports}.{ifname}.{counter}"
    return tmpl.format(ports=metric_prefix_for_ports(sysname),
                       ifname=escape_metric_name(ifname),
                       counter=escape_metric_name(counter))


def metric_path_for_bandwith(sysname, is_percent):
    tmpl = "{system}.bandwidth{percent}"
    return tmpl.format(system=metric_prefix_for_system(sysname),
                       percent="_percent" if is_percent else "")


def metric_path_for_bandwith_peak(sysname, is_percent):
    tmpl = "{system}.bandwidth_peak{percent}"
    return tmpl.format(system=metric_prefix_for_system(sysname),
                       percent="_percent" if is_percent else "")


def metric_path_for_cpu_load(sysname, cpu_name, interval):
    tmpl = "{cpu}.{cpu_name}.loadavg{interval}min"
    return tmpl.format(cpu=metric_prefix_for_cpu(sysname),
                       cpu_name=escape_metric_name(cpu_name),
                       interval=escape_metric_name(str(interval)))


def metric_path_for_cpu_utilization(sysname, cpu_name):
    tmpl = "{cpu}.{cpu_name}.utilization"
    return tmpl.format(cpu=metric_prefix_for_cpu(sysname),
                       cpu_name=escape_metric_name(cpu_name))


def metric_path_for_sysuptime(sysname):
    tmpl = "{system}.sysuptime"
    return tmpl.format(system=metric_prefix_for_system(sysname))


def metric_prefix_for_cpu(sysname):
    tmpl = "{device}.cpu"
    return tmpl.format(device=metric_prefix_for_device(sysname))


def metric_prefix_for_memory(sysname, memory_name):
    tmpl = "{device}.memory.{memname}"
    return tmpl.format(device=metric_prefix_for_device(sysname),
                       memname=escape_metric_name(memory_name))


def metric_prefix_for_system(sysname):
    tmpl = "{device}.system"
    return tmpl.format(device=metric_prefix_for_device(sysname))


def metric_prefix_for_ports(sysname):
    tmpl = "{device}.ports"
    return tmpl.format(device=metric_prefix_for_device(sysname))

def metric_prefix_for_device(sysname):
    tmpl = "nav.devices.{sysname}"
    if hasattr(sysname, 'sysname'):
        sysname = sysname.sysname
    return tmpl.format(sysname=escape_metric_name(sysname))
