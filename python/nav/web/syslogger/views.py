# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""syslogger view definitions"""

import json
import datetime
from configparser import ConfigParser

from django.db.models.aggregates import Count
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse

from nav.config import NAV_CONFIG, find_config_file

from nav.web.auth.utils import get_account

from nav.models.logger import LogMessage
from nav.models.logger import ErrorError
from nav.web.syslogger.forms import LoggerGroupSearchForm
from nav.web.utils import create_title, is_ajax


DATEFORMAT = "%Y-%m-%d %H:%M:%S"

try:
    DOMAIN_SUFFICES = NAV_CONFIG.get("DOMAIN_SUFFIX", "").split(",")
except IOError:
    DOMAIN_SUFFICES = []
DOMAIN_SUFFICES = [s.strip() for s in DOMAIN_SUFFICES]


def _strip_empty_arguments(request):
    """Strips empty arguments and their related operator arguments from the
    QueryDict in request.GET and returns a new, possibly modified QueryDict.

    """
    query = request.GET.copy()

    deletable = [key for key, value in query.items() if not value.strip()]
    for key in deletable:
        del query[key]
    return query


def _build_context(request):
    nav_path = [('Home', '/'), ('Syslogger', reverse('logger_index'))]
    results = []
    context = {}
    aggregates = {}

    if request.GET:
        query_dict = request.GET.copy()

        form = LoggerGroupSearchForm(query_dict)
        if form.is_valid():
            results = LogMessage.objects.filter(
                time__gte=form.cleaned_data['timestamp_from'],
                time__lte=form.cleaned_data['timestamp_to'],
            ).select_related()
            if form.cleaned_data.get('priority', None):
                priority_keyword = form.cleaned_data['priority']
                if not isinstance(form.cleaned_data['priority'], list):
                    priority_keyword = [form.cleaned_data['priority']]

                results = results.filter(newpriority__keyword__in=priority_keyword)

            if form.cleaned_data.get('mnemonic', None):
                message_type_mnemonic = form.cleaned_data['mnemonic']
                if not isinstance(form.cleaned_data['mnemonic'], list):
                    message_type_mnemonic = [form.cleaned_data['mnemonic']]

                results = results.filter(type__mnemonic__in=message_type_mnemonic)

            if form.cleaned_data.get('facility', None):
                message_type_facility = form.cleaned_data['facility']
                if not isinstance(form.cleaned_data['facility'], list):
                    message_type_facility = [form.cleaned_data['facility']]

                results = results.filter(type__facility__in=message_type_facility)

            if form.cleaned_data["category"]:
                categories = form.cleaned_data['category']
                if not isinstance(form.cleaned_data['category'], list):
                    categories = [form.cleaned_data['category']]

                results = results.filter(origin__category__in=categories)

            if 'origin' in form.cleaned_data and form.cleaned_data['origin']:
                origin_name = form.cleaned_data['origin']
                if not isinstance(form.cleaned_data['origin'], list):
                    origin_name = [form.cleaned_data['origin']]

                results = results.filter(origin__name__in=origin_name)

            priorities = results.values('newpriority__keyword').annotate(
                sum=Count('newpriority__keyword')
            )
            priorities_headers = ['Priority']
            message_types = results.values(
                'type__facility', 'type__priority__keyword', 'type__mnemonic'
            ).annotate(sum=Count('type'))
            message_types_headers = ['Facility', 'Priority', 'State']
            origins = results.values('origin__name').annotate(sum=Count('origin__name'))
            origins_headers = ['Origin']

            aggregates.update(
                {
                    'Priorities': {
                        'values': priorities,
                        'headers': priorities_headers,
                        'colspan': 1,
                    }
                }
            )
            aggregates.update(
                {
                    'Type': {
                        'values': message_types,
                        'headers': message_types_headers,
                        'colspan': 3,
                    }
                }
            )
            aggregates.update(
                {
                    'Origin': {
                        'values': origins,
                        'headers': origins_headers,
                        'colspan': 1,
                    }
                }
            )

            def _update_show_log_context(value, results):
                if value:
                    context.update({'log_messages': results})
                    context.update({'show_log': value})
                form.data = form.data.copy()  # mutable QueryDict, yes please
                form.data['show_log'] = value

            if form.cleaned_data.get('show_log', None):
                show_log = bool(form.cleaned_data['show_log'])
                _update_show_log_context(show_log, results)

            if len(priorities) <= 1 and len(origins) <= 1:
                _update_show_log_context(True, results)
            elif len(message_types) <= 1 and len(priorities) <= 1:
                _update_show_log_context(True, results)

    else:
        initial_context = {
            'timestamp_from': (datetime.datetime.now() - datetime.timedelta(days=1)),
            'timestamp_to': datetime.datetime.now(),
        }
        form = LoggerGroupSearchForm(initial=initial_context)

    strip_query_args = _strip_empty_arguments(request)
    strip_query_args = strip_query_args.urlencode() if strip_query_args else ""

    context.update(
        {
            'form': form,
            'bookmark': "{0}?{1}".format(reverse(index), strip_query_args),
            'aggregates': aggregates,
            'timestamp': datetime.datetime.now().strftime(DATEFORMAT),
            'domain_strip': json.dumps(DOMAIN_SUFFICES),
            'navpath': nav_path,
            'title': create_title(nav_path),
        }
    )
    return context


def handle_search(request, _searchform, form_target):
    account = get_account(request)
    if not account:
        return HttpResponseForbidden("You must be logged in to access this resource")

    context = _build_context(request)

    context.update({'form_target': form_target})

    return render(request, 'syslogger/frag-search.html', context)


def index(request):
    return render(request, 'syslogger/index.html', _build_context(request))


def group_search(request):
    if not is_ajax(request):
        return HttpResponseRedirect(reverse(index) + '?' + request.GET.urlencode())
    return handle_search(request, LoggerGroupSearchForm, reverse(group_search))


def exceptions_response(request):
    """
    Handler for exception-mode.
    """
    if not is_ajax(request):
        return HttpResponseRedirect(reverse(index) + '?' + request.GET.urlencode())

    account = get_account(request)
    if not account:
        return HttpResponseRedirect('/')
    config = ConfigParser()
    config.read(find_config_file('logger.conf'))
    options = config.options("priorityexceptions")
    excepts = []
    context = {}
    for option in options:
        newpriority = config.get("priorityexceptions", option)
        excepts.append((option, newpriority))
    context['exceptions'] = excepts
    context['exceptions_mode'] = True
    return render(request, 'syslogger/frag-exceptions.html', context)


def errors_response(request):
    """
    Handler for error-mode.
    """
    if not is_ajax(request):
        return HttpResponseRedirect(reverse(index) + '?' + request.GET.urlencode())

    account = get_account(request)
    if not account:
        return HttpResponseRedirect('/')
    context = {}
    errs = []
    for err in ErrorError.objects.all():
        errs.append(err.message)
    context['errors'] = errs
    context['errors_count'] = len(errs)
    context['errors_mode'] = True
    return render(request, 'syslogger/frag-errors.html', context)
