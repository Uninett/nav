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
import urllib2
import simplejson
from urlparse import urljoin
from urllib import urlencode
import itertools
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

[graphiteweb]
base=http://localhost:8000/
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


##############################
# metrics search & discovery #
##############################

def get_all_leaves_below(top, ignored=None):
    """Gets a list of all leaf nodes in the metric hierarchy below top"""
    walker = nodewalk(top, ignored)
    paths = (leaves for (name, nonleaves, leaves) in walker)
    return list(itertools.chain(*paths))


def nodewalk(top, ignored=None):
    """Walks through a graphite metric hierarchy.

    Basically works like os.walk()

    :param top: Path to the node to walk from.
    :param ignored: A list of node IDs to completely ignore.
    :returns: A generator that generates three-tuples of
              (name, nonleaves, leaves)

    """
    ignored = ignored or []
    nodes = raw_metric_query(top + '.*')
    nonleaves, leaves = [], []
    for node in nodes:
        if node['id'] in ignored:
            continue
        if node.get('leaf', False):
            leaves.append(node['id'])
        else:
            nonleaves.append(node['id'])

    yield top, nonleaves, leaves

    for name in nonleaves:
        for x in nodewalk(name):
            yield x


def get_metric_nonleaf_children(path):
    """Returns a list of available graphite non-leaf nodes just below path.

    :param path: A path to a Graphite metric.
    :returns: A list of metric paths.

    """
    query = path + ".*"
    data = raw_metric_query(query)
    result = [node['id'] for node in data
              if not node.get('leaf', False)]
    return result


def get_metric_leaf_children(path):
    """Returns a list of available graphite leaf nodes just below path.

    :param path: A path to a Graphite metric.
    :returns: A list of metric paths.

    """
    query = path + ".*"
    data = raw_metric_query(query)
    result = [node['id'] for node in data
              if node.get('leaf', False)]
    return result


def raw_metric_query(query):
    """Runs a query for metric information against Graphite's REST API.

    :param query: A search string, e.g. "nav.devices.some-gw_example_org.*"
    :returns: A list of matching metrics, each represented by a dict.

    """
    base = CONFIG.get("graphiteweb", "base")
    base = urljoin(base, "/metrics/find")
    query = urlencode({'query': query})
    url = "%s?%s" % (base, query)

    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req)
        return simplejson.load(response)
    finally:
        response.close()


##########################
# metrics data retrieval #
##########################

def get_metric_average(target, start="-5min", end="now", ignore_unknown=True):
    """Calculates the average value of a metric over a given period of time

    :param target: A metric path string or a list of multiple metric paths
    :param start: A start time specification that Graphite will accept.
    :param end: An end time specification that Graphite will accept.
    :param ignore_unknown: Ignore unknown values when calculating the average.
                           Unless True, any unknown data in the series will
                           result in an average value of None.
    :returns: A dict of {target: average_value} items. Targets that weren't
              found in Graphite will not be present in the dict.

    """
    data = get_metric_data(target, start, end)
    result = {}
    for target in data:
        dpoints = [d[0] for d in target['datapoints']
                   if not (ignore_unknown and d[0] is None)]
        if None in dpoints:
            avg = None
        else:
            avg = sum(dpoints) / len(dpoints)
        result[target['target']] = avg
    return result


def get_metric_data(target, start="-5min", end="now"):
    """
    Retrieves datapoints from a graphite metric for a given period of time.

    :param target: A metric path string or a list of multiple metric paths
    :param start: A start time specification that Graphite will accept.
    :param end: An end time specification that Graphite will accept.

    :returns: A raw, response from Graphite. Normally a list of dicts that
              represent the names and datapoints of each matched target,
              like so::

                  [{'target': 'x', 'datapoints': [(value, timestamp), ...]}]

    """
    base = CONFIG.get("graphiteweb", "base")
    base = urljoin(base, "/render/")

    query = {
        'target': target,
        'from': start,
        'until': end,
        'format': 'json',
    }
    query = urlencode(query, True)
    url = "%s?%s" % (base, query)

    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req)
        return simplejson.load(response)
    finally:
        response.close()


#########################
# metric path templates #
#########################
# pylint: disable=C0111

def metric_path_for_packet_loss(sysname):
    tmpl = "{device}.ping.packetLoss"
    return tmpl.format(device=metric_prefix_for_device(sysname))


def metric_path_for_roundtrip_time(sysname):
    tmpl = "{device}.ping.roundTripTime"
    return tmpl.format(device=metric_prefix_for_device(sysname))


def metric_path_for_service_availability(sysname, handler, service_id):
    tmpl = "{service}.availability"
    return tmpl.format(
        service=metric_prefix_for_service(sysname, handler, service_id))


def metric_path_for_service_response_time(sysname, handler, service_id):
    tmpl = "{service}.responseTime"
    return tmpl.format(
        service=metric_prefix_for_service(sysname, handler, service_id))


def metric_prefix_for_service(sysname, handler, service_id):
    tmpl = "{device}.services.{handler}_{service_id}"
    return tmpl.format(device=metric_prefix_for_device(sysname),
                       handler=handler, service_id=service_id)


def metric_path_for_sensor(sysname, sensor):
    tmpl = "{device}.sensors.{sensor}"
    return tmpl.format(device=metric_prefix_for_device(sysname),
                       sensor=escape_metric_name(sensor))


def metric_path_for_interface(sysname, ifname, counter):
    tmpl = "{interface}.{counter}"
    return tmpl.format(interface=metric_prefix_for_interface(sysname, ifname),
                       counter=escape_metric_name(counter))


def metric_prefix_for_interface(sysname, ifname):
    tmpl = "{ports}.{ifname}"
    return tmpl.format(ports=metric_prefix_for_ports(sysname),
                       ifname=escape_metric_name(ifname))


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


def metric_prefix_for_prefix(netaddr):
    tmpl = "nav.prefixes.{netaddr}"
    if hasattr(netaddr, 'net_address'):
        netaddr = netaddr.net_address
    return tmpl.format(netaddr=escape_metric_name(netaddr))


def metric_path_for_prefix(netaddr, metric_name):
    tmpl = "{prefix}.{metric_name}"
    return tmpl.format(prefix=metric_prefix_for_prefix(netaddr),
                       metric_name=escape_metric_name(metric_name))
