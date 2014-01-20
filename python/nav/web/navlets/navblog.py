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
"""Feed reader widget"""

import feedparser
from django.http import HttpResponse
from nav.django.utils import get_account
from nav.models.profiles import AccountNavlet
from nav.web.navlets import Navlet, NAVLET_MODE_VIEW


class NavBlogNavlet(Navlet):
    """Widget for displaying feeds"""

    title = "NAV Blog"
    description = "Displays entries from the NAV blog"
    refresh_interval = 1000 * 60 * 10  # Refresh every 10 minutes
    highlight = True

    def get_template_basename(self):
        return "navblog"

    def get_context_data(self, **kwargs):
        context = super(NavBlogNavlet, self).get_context_data(**kwargs)
        blogurl = 'http://blog.nav.uninett.no/rss'
        maxposts = 5

        feed = feedparser.parse(blogurl)
        feed['maxentries'] = feed['entries'][:maxposts]

        context.update({
            'feed': feed,
        })
        return context
