# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Uninett AS
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
"""radius accounting interface views"""

from django.shortcuts import render
from django.urls import reverse
from nav.web.modals import render_modal
from nav.web.utils import create_title
from .forms import AccountChartsForm, AccountLogSearchForm, ErrorLogSearchForm

from .radius_config import (
    INDEX_PAGE,
    LOG_SEARCHRESULTFIELDS,
    ACCT_DETAILSFIELDS,
    ACCT_DBFIELDSDESCRIPTIONS,
    LOG_DETAILFIELDS,
    LOG_FIELDDESCRIPTIONS,
)

from .db import (
    AcctChartsQuery,
    AcctDetailQuery,
    AcctSearchQuery,
    LogDetailQuery,
    LogSearchQuery,
)


def get_navpath(path):
    """Add path to root path.

    :type path: tuple
    """
    navpath = [('Home', '/'), ('Radius', reverse('radius-index'))]
    return navpath + [path]


def index(request):
    """
    Start page based on configuration.
    Uses redirect to get the whole urls
    """
    if INDEX_PAGE == 'acctcharts':
        return account_charts(request)
    elif INDEX_PAGE == 'logsearch':
        return log_search(request)
    else:
        return account_search(request)


def account_log_hints_modal(request):
    """Displays a modal with hints for account log search"""
    return render_modal(
        request,
        'radius/_account_log_hints_modal.html',
        modal_id="account-log-hints",
        size="large",
    )


def log_search(request):
    """Displays the page for doing a radius log search"""
    context = {}

    if 'send' in request.GET:
        form = ErrorLogSearchForm(request.GET)
        if form.is_valid():
            data = form.cleaned_data
            searchstring = data.get('query')[1]
            searchtype = data.get('query')[0]

            hours = timestamp = slack = ''
            time = data.get('time')
            timemode = time[0] if time and len(time) == 2 else ''
            if timemode == 'hours':
                hours = time[1]
            elif timemode == 'timestamp':
                timestamp, slack = split_time(time[1])

            query = LogSearchQuery(
                searchstring,
                searchtype,
                data.get('log_entry_type'),
                timemode,
                timestamp,
                slack,
                hours,
                'time',
                'DESC',
            )
            query.execute()

            field_desc = [
                LOG_FIELDDESCRIPTIONS[field] for field in LOG_SEARCHRESULTFIELDS
            ]

            context.update({'field_desc': field_desc, 'result': query.result})
        else:
            context['errors'] = form.errors
    else:
        form = ErrorLogSearchForm()

    navpath = get_navpath(('Error Log',))
    context.update(
        {
            'navpath': navpath,
            'title': create_title(navpath),
            'form': form,
            'logsearch': True,
        }
    )

    return render(request, 'radius/error_log.html', context)


def log_search_hints_modal(request):
    """Displays a modal with hints for log search"""
    return render_modal(
        request,
        'radius/_error_log_hints_modal.html',
        modal_id="error-log-hints",
        size="large",
    )


def log_detail_page(request, accountid):
    """Displays log details as a separate page"""
    template = 'radius/detail.html'
    return log_detail(request, accountid, template)


def log_detail_modal(request, accountid):
    """Displays log details as a separate page"""
    template = 'radius/detail_modal.html'
    return log_detail(request, accountid, template, use_modal=True)


def log_detail(request, accountid, template, use_modal=False):
    """Displays log details for accountid with the given template"""
    query = LogDetailQuery(accountid)
    query.execute()

    fields = []
    if query.result:
        result = query.result[0]
        field_desc = [LOG_FIELDDESCRIPTIONS[field] for field in LOG_DETAILFIELDS]
        fields = zip(field_desc, result)

    context = {
        'fields': fields,
        'result': query.result,
        'reverse': reverse('radius-log_detail', args=(accountid,)),
    }

    if use_modal:
        return render_modal(
            request,
            template,
            context=context,
            modal_id="log-detail",
        )

    navpath = get_navpath(('Log Detail',))
    context.update(
        {
            'title': create_title(navpath),
            'navpath': navpath,
        }
    )

    return render(request, template, context)


def account_charts(request):
    """Displays the page for account charts"""
    context = {}

    if 'send' in request.GET:
        form = AccountChartsForm(request.GET)
        if form.is_valid():
            days = form.cleaned_data['days']
            tables = []
            for chart in form.cleaned_data['charts']:
                query = AcctChartsQuery(chart, days)
                query.execute()
                tables.append((query.table_title, query.result))
            context['tables'] = tables

    else:
        form = AccountChartsForm()

    navpath = get_navpath(('Account Charts',))
    context.update(
        {
            'navpath': navpath,
            'title': create_title(navpath),
            'form': form,
            'acctcharts': True,
        }
    )

    return render(request, 'radius/account_charts.html', context)


def account_chart_hints_modal(request):
    """Displays a modal with hints for account charts"""
    return render_modal(
        request,
        'radius/_account_chart_hints_modal.html',
        modal_id="account-chart-hints",
        size="large",
    )


def account_detail_page(request, accountid):
    """Displays account details as a separate page"""
    template = 'radius/detail.html'
    return account_detail(request, accountid, template)


def account_detail_modal(request, accountid):
    """Displays account details suitable for a modal"""
    template = 'radius/detail_modal.html'
    return account_detail(request, accountid, template, use_modal=True)


def account_detail(request, accountid, template, use_modal=False):
    """Finds account details for a specific accountid"""
    query = AcctDetailQuery(accountid)
    query.execute()

    fields = []
    if query.result:
        result = query.result[0]
        field_desc = [ACCT_DBFIELDSDESCRIPTIONS[field] for field in ACCT_DETAILSFIELDS]
        fields = zip(field_desc, result)

    context = {
        'fields': fields,
        'result': query.result,
        'reverse': reverse('radius-account_detail', args=(accountid,)),
    }

    if use_modal:
        return render_modal(
            request,
            template,
            context=context,
            modal_id="account-detail",
        )

    navpath = get_navpath(('Account Detail',))
    context.update(
        {
            'title': create_title(navpath),
            'navpath': navpath,
        }
    )

    return render(request, template, context)


def account_search(request):
    """Displays the page for doing an account log search"""
    context = {}

    if 'send' in request.GET:
        form = AccountLogSearchForm(request.GET)
        if form.is_valid():
            data = form.cleaned_data

            days = timestamp = slack = ''
            time = data.get('time')
            timemode = time[0] if time and len(time) == 2 else ''
            if timemode == 'days':
                days = time[1]
            elif timemode == 'timestamp':
                timestamp, slack = split_time(time[1])

            dns_lookup = data.get('dns_lookup')

            query = AcctSearchQuery(
                data.get('query')[1],
                data.get('query')[0],
                data.get('port_type'),
                timemode,
                timestamp,
                slack,
                days,
                'userdns' in dns_lookup,
                'nasdns' in dns_lookup,
                'acctstarttime',
                'DESC',
            )
            query.execute()
            (total_time, total_sent, total_received) = query.make_stats()
            context.update(
                {
                    'result': query.result,
                    'total_time': total_time,
                    'total_sent': total_sent,
                    'total_received': total_received,
                }
            )
        else:
            context['errors'] = form.errors
    else:
        form = AccountLogSearchForm()

    navpath = get_navpath(('Account Log',))
    context.update(
        {
            'title': create_title(navpath),
            'navpath': navpath,
            'form': form,
            'acctsearch': True,
        }
    )

    return render(request, 'radius/account_log.html', context)


def split_time(timestring):
    """Splits timestrin in timestamp and optional slack. Default slack is 1"""
    time_values = timestring.split('|')
    timestamp = time_values[0]
    slack = 1
    if len(time_values) > 1:
        slack = time_values[1]
    return timestamp, slack
