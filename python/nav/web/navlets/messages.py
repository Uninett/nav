#
# Copyright (C) 2013 Uninett AS
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

from nav.web.navlets import Navlet
from nav.web.webfront.utils import current_messages


class MessagesNavlet(Navlet):
    title = 'Messages'
    description = 'Displays messages given by NAV admins'
    refresh_interval = 60 * 1000

    def get_template_basename(self):
        return 'messages'

    def get_context_data(self, **kwargs):
        context = super(MessagesNavlet, self).get_context_data(**kwargs)
        context['current_messages'] = current_messages()

        return context
