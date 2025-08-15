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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Exceptions and errors related to dhcpstats."""

from nav.errors import GeneralException


class CommunicationError(GeneralException):
    """Communication error"""


class KeaUnexpected(CommunicationError):
    """An unexpected error occurred when communicating with Kea"""


class KeaError(CommunicationError):
    """Kea API failed during command processing"""


class KeaUnsupported(CommunicationError):
    """Command not supported by Kea API"""


class KeaEmpty(CommunicationError):
    """Requested resource not found by Kea API"""


class KeaConflict(CommunicationError):
    """
    Kea API failed to apply requested changes due to conflicts with
    its internal state
    """
