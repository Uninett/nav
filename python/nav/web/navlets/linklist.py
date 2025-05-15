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

import math

from nav.config import read_flat_config
from nav.web.navlets import Navlet
from nav.web.webfront import NAV_LINKS_PATH


class LinkListNavlet(Navlet):
    title = "Links"
    description = "Displays a list of links from the admins"

    def get_context_data(self, **kwargs):
        context = super(LinkListNavlet, self).get_context_data(**kwargs)

        nav_links = read_flat_config(NAV_LINKS_PATH)
        context['nav_links'] = nav_links
        context['half'] = math.ceil(len(nav_links) / 2.0)
        return context

    def get_template_basename(self):
        return "linklist"
