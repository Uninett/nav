#
# Copyright (C) 2025 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Type definitions for nav.mibs package."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LogicalMibInstance:
    """A MIB instance identifier.

    Some devices (like Cisco switches) provide multiple logical instances of a MIB (such
    as BRIDGE-MIB) within a single physical device, and we need a way to reference them
    and the settings needed to collect data from a specific logical instance.
    """

    description: str
    community: Optional[str]
    context: Optional[str] = None
    context_engine_id: Optional[bytes] = None
