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
"""Widget for displaying a chart"""

import urlparse
from django.http import HttpResponse
from django import forms
from nav.models.profiles import AccountNavlet
from . import Navlet, NAVLET_MODE_EDIT, REFRESH_INTERVAL


class GraphEditForm(forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput)
    url = forms.CharField(label='URL to image')
    target = forms.CharField(required=False,
                             label='Target URL when clicked')
    refresh_interval = forms.IntegerField(min_value=10,
        label='Refresh interval in seconds (requires reload of page)')
    show_controls = forms.BooleanField(required=False,
                                       label='Show time interval controls')

    def clean_refresh_interval(self):
        refresh_interval = self.cleaned_data.get('refresh_interval', 600)
        refresh_interval *= 1000
        return refresh_interval


class GraphWidget(Navlet):
    """Widget for displaying a chart (formerly known as graph)"""

    title = 'Chart'
    description = 'Displays a chart from the Graphite backend'
    is_editable = True
    is_title_editable = True
    refresh_interval = 1000 * 60 * 10
    image_reload = True

    def get_template_basename(self):
        return 'graph'

    def get_context_data(self, **kwargs):
        context = super(GraphWidget, self).get_context_data(**kwargs)
        show_controls = self.preferences.get('show_controls')
        context['hide_buttons'] = 'false' if show_controls else 'true'

        url = title = None
        if self.preferences and 'url' in self.preferences:
            url = self.preferences['url']
            title = self.get_title()

        context['graph_url'] = url
        if title:
            self.title = title

        if self.mode == NAVLET_MODE_EDIT:
            navlet = AccountNavlet.objects.get(pk=self.navlet_id)
            data = navlet.preferences
            data['id'] = self.navlet_id
            data[REFRESH_INTERVAL] = navlet.preferences[REFRESH_INTERVAL] / 1000
            context['form'] = GraphEditForm(data=data)
        return context

    @staticmethod
    def post(request):
        """Display form for adding an url to a chart"""
        account = request.account
        form = GraphEditForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            account_navlet = AccountNavlet.objects.get(pk=cleaned_data['id'], account=account)
            del cleaned_data['id']
            account_navlet.preferences = cleaned_data
            account_navlet.save()
            return HttpResponse()
        else:
            return HttpResponse(form.errors.as_json(), status=400)


    def get_title(self):
        if 'title' in self.preferences:
            return self.preferences['title']
        else:
            return self.get_title_from_url(self.preferences['url'])

    @staticmethod
    def get_title_from_url(url):
        parsed_url = urlparse.urlparse(url)
        query = urlparse.parse_qs(parsed_url.query)
        if 'title' in query:
            return query['title'][0]
