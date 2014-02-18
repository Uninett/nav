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
"""Widget for displaying a graph"""

from django.http import HttpResponse

from nav.models.profiles import AccountNavlet
from . import Navlet


class GraphWidget(Navlet):
    """Widget for displaying a graph"""

    title = 'Graph'
    description = 'Displays a graph from the Graphite backend'
    is_editable = True
    refresh_interval = 1000 * 60 * 10

    def get_template_basename(self):
        return 'graph'

    def get_context_data(self, **kwargs):
        context = super(GraphWidget, self).get_context_data(**kwargs)

        url = None
        if self.preferences and 'url' in self.preferences:
            url = self.preferences['url']
        context['graph_url'] = url
        return context

    @staticmethod
    def post(request):
        """Display form for adding an url to a graph"""
        account = request.account
        nid = int(request.POST.get('id'))
        url = request.POST.get('url')

        account_navlet = AccountNavlet.objects.get(pk=nid, account=account)
        account_navlet.preferences = {'url': url}
        account_navlet.save()

        return HttpResponse()
