#
# Copyright (C) 2013 Uninett AS
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
"""
Metric naming templates for various things that NAV sends/retrieves from
Graphite.
"""

from nav.metrics.names import escape_metric_name
import IPy


def metric_prefix_for_ipdevpoll_job(sysname, job_name):
    tmpl = "{device}.ipdevpoll.{job_name}"
    return tmpl.format(
        device=metric_prefix_for_device(sysname), job_name=escape_metric_name(job_name)
    )


def metric_path_for_bandwith(sysname, is_percent):
    tmpl = "{system}.bandwidth{percent}"
    return tmpl.format(
        system=metric_prefix_for_system(sysname),
        percent="_percent" if is_percent else "",
    )


def metric_path_for_bandwith_peak(sysname, is_percent):
    tmpl = "{system}.bandwidth_peak{percent}"
    return tmpl.format(
        system=metric_prefix_for_system(sysname),
        percent="_percent" if is_percent else "",
    )


def metric_path_for_cpu_load(sysname, cpu_name, interval):
    tmpl = "{cpu}.{cpu_name}.loadavg{interval}min"
    return tmpl.format(
        cpu=metric_prefix_for_cpu(sysname),
        cpu_name=escape_metric_name(cpu_name),
        interval=escape_metric_name(str(interval)),
    )


def metric_path_for_cpu_utilization(sysname, cpu_name):
    tmpl = "{cpu}.{cpu_name}.utilization"
    return tmpl.format(
        cpu=metric_prefix_for_cpu(sysname), cpu_name=escape_metric_name(cpu_name)
    )


def metric_path_for_interface(sysname, ifname, counter):
    tmpl = "{interface}.{counter}"
    return tmpl.format(
        interface=metric_prefix_for_interface(sysname, ifname),
        counter=escape_metric_name(counter),
    )


def metric_path_for_packet_loss(sysname):
    tmpl = "{device}.ping.packetLoss"
    return tmpl.format(device=metric_prefix_for_device(sysname))


def metric_path_for_prefix(netaddr, metric_name):
    tmpl = "{prefix}.{metric_name}"
    return tmpl.format(
        prefix=metric_prefix_for_prefix(netaddr),
        metric_name=escape_metric_name(metric_name),
    )


def metric_path_for_roundtrip_time(sysname):
    tmpl = "{device}.ping.roundTripTime"
    return tmpl.format(device=metric_prefix_for_device(sysname))


def metric_prefix_for_sensors(sysname):
    tmpl = "{device}.sensors"
    return tmpl.format(device=metric_prefix_for_device(sysname))


def metric_path_for_sensor(sysname, sensor):
    tmpl = "{prefix}.{sensor}"
    return tmpl.format(
        prefix=metric_prefix_for_sensors(sysname), sensor=escape_metric_name(sensor)
    )


def metric_path_for_service_availability(sysname, handler, service_id):
    tmpl = "{service}.availability"
    return tmpl.format(service=metric_prefix_for_service(sysname, handler, service_id))


def metric_path_for_service_response_time(sysname, handler, service_id):
    tmpl = "{service}.responseTime"
    return tmpl.format(service=metric_prefix_for_service(sysname, handler, service_id))


def metric_path_for_sysuptime(sysname):
    tmpl = "{system}.sysuptime"
    return tmpl.format(system=metric_prefix_for_system(sysname))


def metric_path_for_power(sysname, index):
    tmpl = "{system}.power.{index}"
    return tmpl.format(system=metric_prefix_for_system(sysname), index=index)


def metric_prefix_for_cpu(sysname):
    tmpl = "{device}.cpu"
    return tmpl.format(device=metric_prefix_for_device(sysname))


def metric_prefix_for_device(sysname):
    tmpl = "nav.devices.{sysname}"
    if hasattr(sysname, 'sysname'):
        sysname = sysname.sysname
    return tmpl.format(sysname=escape_metric_name(sysname))


def metric_prefix_for_interface(sysname, ifname):
    tmpl = "{ports}.{ifname}"
    return tmpl.format(
        ports=metric_prefix_for_ports(sysname), ifname=escape_metric_name(ifname)
    )


def metric_prefix_for_memory(sysname, memory_name):
    tmpl = "{device}.memory.{memname}"
    return tmpl.format(
        device=metric_prefix_for_device(sysname),
        memname=escape_metric_name(memory_name),
    )


def metric_prefix_for_ports(sysname):
    tmpl = "{device}.ports"
    return tmpl.format(device=metric_prefix_for_device(sysname))


def metric_prefix_for_prefix(netaddr):
    tmpl = "nav.prefixes.{netaddr}"
    if hasattr(netaddr, 'net_address'):
        netaddr = netaddr.net_address
    return tmpl.format(netaddr=escape_metric_name(netaddr))


def metric_prefix_for_service(sysname, handler, service_id):
    tmpl = "{device}.services.{handler}_{service_id}"
    return tmpl.format(
        device=metric_prefix_for_device(sysname), handler=handler, service_id=service_id
    )


def metric_prefix_for_system(sysname):
    tmpl = "{device}.system"
    return tmpl.format(device=metric_prefix_for_device(sysname))


def metric_prefix_for_multicast_group(group):
    tmpl = "nav.multicast.groups.{group}"
    return tmpl.format(group=escape_metric_name(str(group)))


def metric_path_for_multicast_usage(group, sysname):
    tmpl = "{group}.igmp_usage.{sysname}"
    if hasattr(sysname, 'sysname'):
        sysname = sysname.sysname
    return tmpl.format(
        group=metric_prefix_for_multicast_group(group),
        sysname=escape_metric_name(sysname),
    )


def metric_path_for_dhcp_pool(
    ip_version, server_name, pool_name, range_start, range_end, metric_name
):
    tmpl = (
        "nav.dhcp.{ip_version}.pool.{server_name}.{pool_name}."
        "{range_start}.{range_end}.{metric_name}"
    )
    range_start = IPy.IP(range_start).strNormal()
    range_end = IPy.IP(range_end).strNormal()
    return tmpl.format(
        ip_version=escape_metric_name(str(ip_version)),
        server_name=escape_metric_name(server_name),
        pool_name=escape_metric_name(pool_name),
        range_start=escape_metric_name(range_start),
        range_end=escape_metric_name(range_end),
        metric_name=escape_metric_name(metric_name),
    )
