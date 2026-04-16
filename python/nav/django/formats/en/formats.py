#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""NAV's preferred date/time formats — ISO-style for consistent display.

These override Django's built-in en locale formats, preserving NAV's
historical formatting now that USE_L10N is always enabled (Django 5.0+).

Machine-consumed dates (data-sort attributes, API output) use hardcoded
ISO 8601 formats and are not affected by these settings.
"""

DATE_FORMAT = 'Y-m-d'
TIME_FORMAT = 'H:i:s'
DATETIME_FORMAT = 'Y-m-d H:i:s'
SHORT_DATE_FORMAT = 'Y-m-d'
SHORT_DATETIME_FORMAT = 'Y-m-d H:i'
YEAR_MONTH_FORMAT = 'Y-m'
MONTH_DAY_FORMAT = 'm-d'
