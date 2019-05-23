#
# Copyright (C) 2014 Uninett AS
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
"""Module comment"""

from nav.watchdog.util import get_statuses
from nav.watchdog.tests import STATUS_OK
from . import Navlet


class WatchDogWidget(Navlet):
    """Widget for displaying WatchDog status"""

    title = 'WatchDog'
    description = 'Displays important statuses for NAV'
    refresh_interval = 1000 * 60 * 10  # Refresh every 10 minutes

    def get_context_data(self, **kwargs):
        context = super(WatchDogWidget, self).get_context_data(**kwargs)
        context['tests'] = [t for t in get_statuses() if t.status != STATUS_OK]
        return context

    def get_template_basename(self):
        return 'watchdog'
