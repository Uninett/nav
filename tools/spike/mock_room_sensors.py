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
"""Backfill mock temperature values for the environment sensors in one room.

The room info "Sensors" tab (/search/room/<roomid>/#!sensors) and the
dashboard sensor widget show the last day of each sensor. Sensor metrics
are stored at 60 s for 1 day and 5 min for 7 days
(python/nav/etc/graphite/storage-schemas.conf), so the script sends points
at both resolutions.

Each sensor gets its own base temperature and a daily cycle. The values are
a function of the sensor and the timestamp, so running the script again
rewrites the same data. Run it again to move "now" forward.

Usage: uv run python tools/spike/mock_room_sensors.py [room id]
"""

import math
import random
import socket
import sys
import time

from nav.bootstrap import bootstrap_django

bootstrap_django()

from nav.models.manage import Room  # noqa: E402

DEFAULT_ROOM = "100"

MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR

# (max age, step) pairs that match the nav-system retentions
RESOLUTIONS = [
    (DAY, MINUTE),
    (7 * DAY, 5 * MINUTE),
]


def noise(name, timestamp, spread):
    """Returns a value in [-spread, spread] that depends only on the input"""
    return random.Random(f"{name}{timestamp}").uniform(-spread, spread)


def temperature(name, timestamp):
    """Returns a temperature between about 5 and 40 degrees.

    The base temperature and the size of the daily cycle depend on the
    sensor name, so each sensor gets its own level.
    """
    rng = random.Random(name)
    base = rng.uniform(8, 32)
    swing = rng.uniform(0.5, 4)
    hour = time.localtime(timestamp).tm_hour + time.localtime(timestamp).tm_min / 60
    cycle = math.sin((hour - 9) / 24 * 2 * math.pi)
    return base + swing * cycle + noise(name, timestamp, 0.3)


def timestamps(now):
    """Returns the timestamps to send, oldest first.

    Each timestamp is a multiple of the step of the most precise archive
    that covers it.
    """
    points = set()
    for max_age, step in RESOLUTIONS:
        start = (now - max_age) // step * step
        points.update(range(start, now + 1, step))
    return sorted(points)


def lines_for(sensors, now):
    """Yields Carbon lines for all sensors"""
    points = timestamps(now)
    for sensor in sensors:
        path = sensor.get_metric_name()
        for timestamp in points:
            yield f"{path} {temperature(path, timestamp):.2f} {timestamp}\n"


def main():
    room = Room.objects.get(pk=sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOM)
    sensors = [
        sensor
        for netbox in room.netboxes.filter(category="ENV").order_by("sysname")
        for sensor in netbox.get_environment_sensors().order_by("id")
    ]
    now = int(time.time()) // MINUTE * MINUTE
    lines = list(lines_for(sensors, now))
    with socket.create_connection(("graphite", 2003)) as sock:
        sock.sendall("".join(lines).encode())
    print(f"Sent {len(lines)} values for {len(sensors)} sensors in room {room.id}")
    for sensor in sensors:
        print(f"  {sensor.netbox.sysname} {sensor.human_readable}")


if __name__ == "__main__":
    main()
