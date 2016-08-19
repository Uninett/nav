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
"""Controllers and Forms for prefix details page"""

from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from nav.web import utils
from nav.models.manage import Prefix, Usage, PrefixUsage


### Forms

class PrefixSearchForm(forms.Form):
    """Form for searching for prefixes"""
    query = forms.CharField(label='Search for prefix')


class PrefixUsageForm(forms.ModelForm):
    """Form to select usages/tags for a prefix"""
    usages = forms.ModelMultipleChoiceField(
        queryset=Usage.objects.all(), label='Add tags',
        widget=forms.SelectMultiple(attrs={'class': 'select2'}))

    def __init__(self, *args, **kwargs):
        super(PrefixUsageForm, self).__init__(*args, **kwargs)
        self.fields['usages'].help_text = ''
        if self.instance.pk:
            self.initial['usages'] = self.instance.usages.all()

    class Meta():
        model = Prefix
        fields = ['usages']


### Controllers

def index(request):
    """Index controller, does not do anything atm"""
    return render(request, 'info/prefix/base.html', get_context())


def prefix_details(request, prefix_id):
    """Controller for rendering prefix details"""
    prefix = get_object_or_404(Prefix, pk=prefix_id)
    context = get_context(prefix)
    context['form'] = PrefixUsageForm(instance=prefix)
    return render(request, 'info/prefix/details.html', context)


@require_POST
def prefix_add_tags(request, prefix_id):
    """Adds usages to a prefix from post data"""
    prefix = Prefix.objects.get(pk=prefix_id)
    existing_usages = {u[0] for u in prefix.usages.values_list()}
    usages = set(request.POST.getlist('usages'))

    to_remove = list(existing_usages - usages)
    to_add = list(usages - existing_usages)

    PrefixUsage.objects.filter(prefix=prefix,
                               usage__in=to_remove).delete()
    for usage_key in to_add:
        usage = Usage.objects.get(pk=usage_key)
        try:
            PrefixUsage(prefix=prefix, usage=usage).save()
        except Exception, err:
            _logger.debug(err)
            pass

    return HttpResponse()


def prefix_reload_tags(request, prefix_id):
    """Render the tags fragment"""
    return render(request, 'info/prefix/frag_tags.html',
                  { 'prefix': Prefix.objects.get(pk=prefix_id) })


### Helpers

def get_context(prefix=None):
    """Returns a object suitable for a breadcrumb"""
    navpath = [('Home', '/'), ('Prefix Details', reverse('prefix-index'))]
    if prefix:
        navpath.append((prefix.net_address,))
    return {
        'prefix': prefix,
        'navpath': navpath,
        'title': utils.create_title(navpath)
    }
