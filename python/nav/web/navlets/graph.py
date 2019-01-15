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
"""Widget for displaying a chart"""

from django.utils.six.moves.urllib.parse import urlparse, parse_qs
from django import forms
from . import Navlet, REFRESH_INTERVAL


class GraphEditForm(forms.Form):
    """Form for editing a graph widget"""
    url = forms.CharField(label='URL to image')
    target = forms.CharField(required=False,
                             label='Target URL when clicked')
    refresh_interval = forms.IntegerField(min_value=10,
        label='Refresh interval in seconds (requires reload of page)')
    show_controls = forms.BooleanField(required=False,
                                       label='Show time interval controls')

    def clean_refresh_interval(self):
        """Convert refresh interval"""
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

    def get_context_data_view(self, context):
        self.title = self.get_title()
        show_controls = self.preferences.get('show_controls')
        context['hide_buttons'] = 'false' if show_controls else 'true'
        context['graph_url'] = self.preferences.get('url')
        return context

    def get_context_data_edit(self, context):
        if self.preferences.get('url'):
            self.preferences[REFRESH_INTERVAL] = self.preferences[
                REFRESH_INTERVAL] / 1000
            context['form'] = GraphEditForm(self.preferences)
        else:
            context['form'] = GraphEditForm(
                initial={REFRESH_INTERVAL: GraphWidget.refresh_interval / 1000})
        return context

    def post(self, request):
        """Display form for adding an url to a chart"""
        form = GraphEditForm(request.POST)
        return super(GraphWidget, self).post(request, form=form)

    def get_title(self):
        """Fetch the title for this widget"""
        if 'title' in self.preferences:
            return self.preferences['title']

        url_title = self.get_title_from_url(self.preferences.get('url'))
        if url_title:
            return url_title

        return GraphWidget.title

    @staticmethod
    def get_title_from_url(url):
        """Get title from url"""
        if not url:
            return
        parsed_url = urlparse(url)
        query = parse_qs(parsed_url.query)
        if 'title' in query:
            return query['title'][0]
