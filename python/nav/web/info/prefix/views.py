#
# Copyright (C) 2016 Uninett AS
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
"""Controllers and Forms for prefix details page"""

from django import forms
from django.db.utils import DatabaseError
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from IPy import IP

from nav.web import utils
from nav.web.auth.utils import get_account
from nav.models.manage import Prefix, Usage, PrefixUsage
from ..forms import SearchForm


### Forms


class PrefixSearchForm(SearchForm):
    """Searchform for prefixes"""

    def __init__(self, *args, **kwargs):
        super(PrefixSearchForm, self).__init__(
            *args, form_action='prefix-index', placeholder='a.b.c.d/e', **kwargs
        )
        self.attrs.form_id = 'prefix-search-form'

    def clean_query(self):
        """Make sure it's something we can use"""
        ip = self.cleaned_data['query']
        try:
            ip = IP(ip)
        except ValueError as error:
            raise forms.ValidationError(
                ('%(error)s'), params={'query': ip, 'error': error}, code='invalid'
            )
        return ip


class PrefixUsageForm(forms.ModelForm):
    """Form to select usages/tags for a prefix"""

    usages = forms.ModelMultipleChoiceField(
        queryset=Usage.objects.all(),
        label='Add tags',
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
    )

    def __init__(self, *args, **kwargs):
        super(PrefixUsageForm, self).__init__(*args, **kwargs)
        self.fields['usages'].help_text = ''
        if self.instance.pk:
            self.initial['usages'] = self.instance.usages.all()

    class Meta(object):
        model = Prefix
        fields = ['usages']


### Helpers


def require_prefix_privilege(func):
    """Decorator for authorizing prefix edit actions"""

    def wrapper(request, *args, **kwargs):
        """Decorator wrapper"""
        if authorize_user(request):
            return func(request, *args, **kwargs)
        else:
            return HttpResponse("User not authorized to edit prefixes", status=403)

    return wrapper


def get_context(prefix=None):
    """Returns a context for a page with a possible prefix"""
    navpath = [
        ('Home', '/'),
        ('Search', reverse('info-search')),
        ('Prefix', reverse('prefix-index')),
    ]
    if prefix:
        navpath.append((prefix.net_address,))
    return {'prefix': prefix, 'navpath': navpath, 'title': utils.create_title(navpath)}


def get_query_results(query):
    """Returns the prefixes determined by the query"""
    where_string = "inet '{}' >>= netaddr".format(IP(query))
    return Prefix.objects.extra(where=[where_string], order_by=['net_address'])


def authorize_user(request):
    """Find out if this user can edit prefixes"""
    account = get_account(request)
    return account.has_perm('web_access', reverse('seeddb-prefix'))


### Controllers


def index(request):
    """Presents user with search form for prefixes"""
    context = get_context()
    query = request.GET.get('query')
    if query:
        form = PrefixSearchForm(request.GET)
        if form.is_valid():
            context['query'] = form.cleaned_data['query']
            context['query_results'] = get_query_results(query)
    else:
        form = PrefixSearchForm()

    context['form'] = form

    if request.htmx:
        return render(request, 'info/prefix/_search_results.html', context)

    return render(request, 'info/prefix/base.html', context)


def prefix_details(request, prefix_id):
    """Controller for rendering prefix details"""
    prefix = get_object_or_404(Prefix, pk=prefix_id)
    context = get_context(prefix)
    context['form'] = PrefixUsageForm(instance=prefix)
    context['can_edit'] = authorize_user(request)

    return render(request, 'info/prefix/details.html', context)


@require_POST
@require_prefix_privilege
def prefix_add_tags(request, prefix_id):
    """Adds usages to a prefix from post data"""
    prefix = Prefix.objects.get(pk=prefix_id)
    existing_usages = {u[0] for u in prefix.usages.values_list()}
    usages = set(request.POST.getlist('usages'))

    to_remove = list(existing_usages - usages)
    to_add = list(usages - existing_usages)

    PrefixUsage.objects.filter(prefix=prefix, usage__in=to_remove).delete()
    for usage_key in to_add:
        usage = Usage.objects.get(pk=usage_key)
        try:
            PrefixUsage(prefix=prefix, usage=usage).save()
        except DatabaseError:
            pass

    return HttpResponse()


def prefix_reload_tags(request, prefix_id):
    """Render the tags fragment"""
    return render(
        request,
        'info/prefix/frag_tags.html',
        {'prefix': Prefix.objects.get(pk=prefix_id)},
    )
