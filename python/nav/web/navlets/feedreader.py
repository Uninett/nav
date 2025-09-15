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
"""Feed reader widget"""

import feedparser
from django.http import HttpResponse
from nav.web.auth.utils import get_account
from nav.models.profiles import AccountNavlet
from nav.web.navlets import Navlet, NAVLET_MODE_VIEW


class FeedReaderNavlet(Navlet):
    """Widget for displaying feeds"""

    title = "FeedReader"
    description = "Reads an RSS or ATOM feed"
    is_editable = True
    refresh_interval = 1000 * 60 * 10  # Refresh every 10 minutes

    def get_template_basename(self):
        return "feedreader"

    def get_context_data(self, **kwargs):
        context = super(FeedReaderNavlet, self).get_context_data(**kwargs)
        blogurl = None
        feed = None
        maxposts = 5

        navlet = AccountNavlet.objects.get(pk=self.navlet_id)
        if navlet.preferences:
            blogurl = navlet.preferences.get('blogurl')
            maxposts = int(navlet.preferences.get('maxposts', maxposts))

        if self.mode == NAVLET_MODE_VIEW and blogurl:
            feed = self._get_feed(blogurl, maxposts)

        context.update({'feed': feed, 'blogurl': blogurl, 'maxposts': maxposts})
        return context

    @staticmethod
    def _get_feed(feedurl, maxposts):
        feed = feedparser.parse(feedurl)
        feed['maxentries'] = feed['entries'][:maxposts]
        return feed

    def post(self, request):
        """Receive blogurl and save it in preferences

        We fetch the account aswell to make sure that people that are not the
        owner but has the id cannot modify the navlet.
        """
        account = get_account(request)
        blogurl = request.POST.get('blogurl')
        maxposts = request.POST.get('maxposts')

        account_navlet = AccountNavlet.objects.get(pk=self.navlet_id, account=account)
        if not account_navlet.preferences:
            account_navlet.preferences = {'blogurl': blogurl, 'maxposts': maxposts}
        else:
            account_navlet.preferences['blogurl'] = blogurl
            account_navlet.preferences['maxposts'] = maxposts
        account_navlet.save()

        return HttpResponse()
