#
# Copyright (C) 2014 UNINETT AS
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
"""Status2 widget"""
import requests
import json
from django.core.urlresolvers import reverse

from nav.models.profiles import AccountNavlet
from . import Navlet

import logging
_logger = logging.getLogger(__name__)


class Status2Widget(Navlet):
    """Widget for displaying status"""

    title = "Status2"
    description = "Shows status for your ip-devices and services"
    refresh_interval = 1000 * 60 * 10  # Refresh every 10 minutes
    is_editable = True

    def get_template_basename(self):
        return "status2"

    def get_context_data(self, **kwargs):
        context = super(Status2Widget, self).get_context_data(**kwargs)
        navlet = AccountNavlet.objects.get(pk=self.navlet_id)
        url = navlet.preferences.get('status_filter')
        context['url'] = reverse('alerthistory-list')

        return context
