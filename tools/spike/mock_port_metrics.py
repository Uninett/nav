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
"""Backfill mock port counters for one interface to Carbon.

The counters are cumulative, like the ones ipdevpoll collects. NAV's graphs
turn them into rates with nonNegativeDerivative. Port metrics are stored at
5 min for 7 days, 30 min for 12 days, 2 h for 50 days and 1 day for 600 days
(python/nav/etc/graphite/storage-schemas.conf). Whisper writes each point to
the most precise archive that covers it, so the script sends points at those
resolutions. That way the Day, Week, Month and Year buttons all show data.

The values are a function of the timestamp, so running the script again
rewrites the same data. Run it again to move "now" forward.

Usage: uv run python tools/spike/mock_port_metrics.py [interface id]
"""

import math
import random
import socket
import sys
import time

from nav.bootstrap import bootstrap_django

bootstrap_django()

from nav.metrics.templates import metric_path_for_interface  # noqa: E402
from nav.models.manage import Interface  # noqa: E402

DEFAULT_INTERFACE = 331721  # uninett-gsw1.uninett.no ge-1/1/0

MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR

# (max age, step) pairs that match the nav-generic retentions
RESOLUTIONS = [
    (7 * DAY, 5 * MINUTE),
    (12 * DAY, 30 * MINUTE),
    (50 * DAY, 2 * HOUR),
    (365 * DAY, DAY),
]

# A poll outage in the last day, so the graphs have a gap to show
GAP = (-6 * HOUR, -4 * HOUR)


def noise(name, timestamp, spread):
    """Returns a factor in [1 - spread, 1 + spread] that depends only on the input"""
    return 1 + random.Random(f"{name}{timestamp}").uniform(-spread, spread)


def daily(timestamp):
    """Returns a factor between 0.2 and 1.0 that peaks in the afternoon"""
    hour = time.localtime(timestamp).tm_hour + time.localtime(timestamp).tm_min / 60
    return 0.6 + 0.4 * math.sin((hour - 8) / 24 * 2 * math.pi)


def rate_in_bits(timestamp):
    return 400e6 * daily(timestamp) * noise("in", timestamp, 0.2)


def rate_out_bits(timestamp):
    return 120e6 * daily(timestamp) * noise("out", timestamp, 0.3)


def burst(name, timestamp, chance, size):
    """Returns `size` for a rare, random share of the timestamps, otherwise 0"""
    return size if random.Random(f"{name}{timestamp}").random() < chance else 0


# Each rate function returns the counter's increase per second
RATES = {
    "ifInOctets": lambda t: rate_in_bits(t) / 8,
    "ifOutOctets": lambda t: rate_out_bits(t) / 8,
    "ifInUcastPkts": lambda t: rate_in_bits(t) / 8 / 800,
    "ifOutUcastPkts": lambda t: rate_out_bits(t) / 8 / 600,
    "ifInMulticastPkts": lambda t: 50 * noise("inmc", t, 0.5),
    "ifOutMulticastPkts": lambda t: 10 * noise("outmc", t, 0.5),
    "ifInBroadcastPkts": lambda t: 5 * noise("inbc", t, 0.8),
    "ifOutBroadcastPkts": lambda t: 1 * noise("outbc", t, 0.8),
    "ifInErrors": lambda t: burst("inerr", t, 0.02, 12),
    "ifOutErrors": lambda t: 0,
    "ifInDiscards": lambda t: 0.5 * noise("indisc", t, 1),
    "ifOutDiscards": lambda t: burst("outdisc", t, 0.05, 3),
}


FINEST = RESOLUTIONS[0][1]


def timestamps(now):
    """Returns (timestamp, step) pairs to send, oldest first.

    Each timestamp gets the step of the most precise archive that covers it.
    """
    points = {}
    for max_age, step in reversed(RESOLUTIONS):
        start = (now - max_age) // step * step
        for timestamp in range(start, now + 1, step):
            points[timestamp] = step
    gap_start, gap_end = now + GAP[0], now + GAP[1]
    return sorted((t, s) for t, s in points.items() if not gap_start <= t < gap_end)


def counter_values(rate, start, now):
    """Returns the counter value at every FINEST step from start to now"""
    values = {}
    value = 0.0
    for timestamp in range(start, now + 1, FINEST):
        values[timestamp] = int(value)
        value += rate(timestamp) * FINEST
    return values


def lines_for(interface, now):
    """Yields Carbon lines for all counters.

    Graphite aggregates port counters by keeping the last value in each slot,
    so a slot of `step` seconds that starts at t holds the counter from
    t + step - FINEST. Points sent directly to a coarse archive get the same
    value, so there is no jump where the coarse and fine archives meet.
    """
    sysname, ifname = interface.netbox.sysname, interface.ifname
    points = timestamps(now)
    for counter, rate in RATES.items():
        path = metric_path_for_interface(sysname, ifname, counter)
        values = counter_values(rate, points[0][0], now + DAY)
        for timestamp, step in points:
            yield f"{path} {values[timestamp + step - FINEST]} {timestamp}\n"


def main():
    interface_id = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INTERFACE
    interface = Interface.objects.select_related("netbox").get(pk=interface_id)
    now = int(time.time()) // (5 * MINUTE) * (5 * MINUTE)
    lines = list(lines_for(interface, now))
    with socket.create_connection(("graphite", 2003)) as sock:
        sock.sendall("".join(lines).encode())
    print(
        f"Sent {len(lines)} values for {len(RATES)} counters on "
        f"{interface.netbox.sysname} {interface.ifname}"
    )


if __name__ == "__main__":
    main()
