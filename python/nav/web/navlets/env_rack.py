#
# Copyright (C) 2016 UNINETT AS
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
"""Module containing EnvironmentRackWidget"""

from . import Navlet


class EnvironmentRackWidget(Navlet):
    """Widget for displaying an environment rack"""

    title = 'Environment rack'
    refresh_interval = 60000  # 60 seconds

    def get_template_basename(self):
        return 'envrack'

    def get_context_data_view(self, context):
        context['rackid'] = self.preferences.get('rackid', 294)
        context['refresh_interval'] = self.preferences.get(
            'refresh_interval', self.refresh_interval)
        return context
