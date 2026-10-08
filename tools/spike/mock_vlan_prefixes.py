#
# Copyright (C) 2026 Sikt
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
"""Backfill mock active IP counts for the prefixes on one VLAN.

The VLAN details page (/search/vlan/<vlanid>/) graphs ip_count for each
prefix as an area, and the sum of ip_range as a "Max addresses" line for
IPv4. collect_active_ip writes ip_count, mac_count and ip_range every 30
minutes. Prefix metrics are stored at 30 min for 30 days, 2 h for 90 days
and 6 h for 600 days (python/nav/etc/graphite/storage-schemas.conf), so the
script sends points at those resolutions.

The counts follow office hours and are lower at weekends. The values are a
function of the prefix and the timestamp, so running the script again
rewrites the same data. Run it again to move "now" forward.

Usage: uv run python tools/spike/mock_vlan_prefixes.py [vlan id]
"""

import math
import random
import socket
import sys
import time

from nav.bootstrap import bootstrap_django

bootstrap_django()

from nav.activeipcollector.manager import find_range  # noqa: E402
from nav.metrics.templates import metric_path_for_prefix  # noqa: E402
from nav.models.manage import Vlan  # noqa: E402

DEFAULT_VLAN = 4638023  # VLAN 1201

MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR

# (max age, step) pairs that match the nav-prefix retentions
RESOLUTIONS = [
    (30 * DAY, 30 * MINUTE),
    (90 * DAY, 2 * HOUR),
    (365 * DAY, 6 * HOUR),
]


def activity(timestamp):
    """Returns a factor between about 0.3 and 1.0 that peaks in office hours"""
    local = time.localtime(timestamp)
    hour = local.tm_hour + local.tm_min / 60
    daily = 0.65 + 0.35 * math.sin((hour - 8) / 24 * 2 * math.pi)
    return daily * (0.5 if local.tm_wday >= 5 else 1.0)


def ip_count(net_address, ip_range, timestamp):
    """Returns the number of active addresses on the prefix.

    The busiest level depends on the prefix. IPv4 prefixes stay below their
    range.
    """
    rng = random.Random(net_address)
    peak = rng.uniform(40, 400)
    if ip_range:
        peak = min(peak, ip_range * rng.uniform(0.5, 0.8))
    jitter = random.Random(f"{net_address}{timestamp}").uniform(-0.05, 0.05)
    return round(peak * (activity(timestamp) + jitter))


def timestamps(now):
    """Returns the timestamps to send, oldest first.

    Each timestamp is a multiple of the step of the most precise archive
    that covers it.
    """
    points = {}
    for max_age, step in reversed(RESOLUTIONS):
        start = (now - max_age) // step * step
        for timestamp in range(start, now + 1, step):
            points[timestamp] = step
    return sorted(points)


def lines_for(prefixes, now):
    """Yields Carbon lines for ip_count, mac_count and ip_range of each prefix"""
    points = timestamps(now)
    for prefix in prefixes:
        net_address = str(prefix.net_address)
        ip_range = find_range(net_address)
        for timestamp in points:
            count = ip_count(net_address, ip_range, timestamp)
            values = {
                "ip_count": count,
                "mac_count": round(count * 0.9),
                "ip_range": ip_range,
            }
            for metric, value in values.items():
                path = metric_path_for_prefix(net_address, metric)
                yield f"{path} {value} {timestamp}\n"


def main():
    vlan = Vlan.objects.get(pk=int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_VLAN)
    prefixes = list(vlan.prefixes.order_by("net_address"))
    now = int(time.time()) // (30 * MINUTE) * (30 * MINUTE)
    lines = list(lines_for(prefixes, now))
    with socket.create_connection(("graphite", 2003)) as sock:
        sock.sendall("".join(lines).encode())
    print(
        f"Sent {len(lines)} values for {len(prefixes)} prefixes "
        f"on VLAN {vlan.vlan} ({vlan.id})"
    )
    for prefix in prefixes:
        print(f"  {prefix.net_address}: range {find_range(str(prefix.net_address))}")


if __name__ == "__main__":
    main()
