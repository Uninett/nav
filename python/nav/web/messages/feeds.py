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

import datetime

from django.contrib.syndication.views import Feed
from django.urls import reverse

from nav.models.msgmaint import Message


class ActiveMessagesFeed(Feed):
    """
    Generates a RSS feed of the active messages in NAV.
    Uses the Django Syndication module and its interface.
    """

    title = "NAV Message feed"
    description = "NAV Message feed"

    def link(self):
        return reverse('messages-active')

    def items(self):
        return Message.objects.filter(
                publish_start__lte=datetime.datetime.now(),
                publish_end__gte=datetime.datetime.now(),
                replaced_by__isnull=True,
            )

    def item_title(self, item):
        return item.title

    def item_pubdate(self, item):
        return item.publish_start

    def item_description(self, item):
        return item.description

    def item_link(self, item):
        return reverse('messages-view', args=[item.pk])
