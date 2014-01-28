# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 University of Tromsø
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""radius accounting interface views"""
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from .forms import (AccountChartsForm,
                    AccountLogSearchForm,
                    ErrorLogSearchForm)

from radius_config import (INDEX_PAGE,
                           LOG_SEARCHRESULTFIELDS,
                           ACCT_DETAILSFIELDS,
                           ACCT_DBFIELDSDESCRIPTIONS,
                           LOG_DETAILFIELDS,
                           LOG_FIELDDESCRIPTIONS)

from .db import (AcctChartsQuery,
                 AcctDetailQuery,
                 AcctSearchQuery,
                 LogDetailQuery,
                 LogSearchQuery)


TITLE = 'NAV - Radius'
NAVPATH = [('Home', '/'), ('Radius', None)]


def index(request):
    """
    Start page based on configuration.
    Uses redirect to get the whole urls
    """
    if INDEX_PAGE == 'acctcharts':
        return HttpResponseRedirect('acctcharts')
    elif INDEX_PAGE == 'logsearch':
        return HttpResponseRedirect('logsearch')
    else:
        return HttpResponseRedirect('acctsearch')


def log_search(request):

    context = {}

    if 'send' in request.GET:
        form = ErrorLogSearchForm(request.GET)
        if form.is_valid():
            data = form.cleaned_data
            searchstring = data.get('query')[1]
            searchtype = data.get('query')[0]

            # TODO? Put this logic in the form itself
            hours = timestamp = slack = ''
            time = data.get('time')
            timemode = time[0] if time and len(time) == 2 else ''
            if timemode == 'hours':
                hours = time[0]
            elif timemode == 'timestamp':
                timestamp, slack = time[1].split('|')

            query = LogSearchQuery(
                searchstring,
                searchtype,
                data.get('log_entry_type'),
                timemode,
                timestamp,
                slack,
                hours,
                'time',
                'DESC'
            )
            query.execute()

            field_desc = [
                LOG_FIELDDESCRIPTIONS[field]
                for field in LOG_SEARCHRESULTFIELDS
            ]

            context.update({
                'field_desc': field_desc,
                'result': query.result
            })
        else:
            context['errors'] = form.errors
    else:
        form = ErrorLogSearchForm()

    context.update({
        'title': TITLE,
        'navpath': NAVPATH,
        'form': form,
        'logsearch': True
    })

    return render_to_response('radius/error_log.html', context,
                              context_instance=RequestContext(request))


def log_detail(request):

    query = LogDetailQuery(request.GET.get('id'))
    query.execute()
    result = query.result[0]

    field_desc = [
        LOG_FIELDDESCRIPTIONS[field]
        for field in LOG_DETAILFIELDS]
    fields = zip(field_desc, result)

    context = {
        'title': TITLE,
        'navpath': NAVPATH,
        'fields': fields,
    }

    return render_to_response('radius/detail.html', context,
                              context_instance=RequestContext(request))


def account_charts(request):

    context = {}

    if 'send' in request.GET:
        form = AccountChartsForm(request.GET)
        if form.is_valid():
            days = form.cleaned_data['days']
            tables = []
            for chart in form.cleaned_data['charts']:
                query = AcctChartsQuery(chart, days)
                query.execute()
                tables.append(
                    (query.table_title, query.result))
            context['tables'] = tables

    else:
        form = AccountChartsForm()

    context.update({
        'title': TITLE,
        'navpath': NAVPATH,
        'form': form,
        'acctcharts': True
    })

    return render_to_response('radius/account_charts.html', context,
                              context_instance=RequestContext(request))


def account_detail(request):

    query = AcctDetailQuery(request.GET.get('acctuniqueid'))
    query.execute()
    result = query.result[0]

    field_desc = [
        ACCT_DBFIELDSDESCRIPTIONS[field]
        for field in ACCT_DETAILSFIELDS]
    fields = zip(field_desc, result)

    context = {
        'title': TITLE,
        'navpath': NAVPATH,
        'fields': fields,
        'result': query.result
    }

    return render_to_response('radius/detail.html', context,
                              context_instance=RequestContext(request))


def account_search(request):

    context = {}

    if 'send' in request.GET:
        form = AccountLogSearchForm(request.GET)
        if form.is_valid():
            data = form.cleaned_data

            # TODO? Put this logic in the form itself
            days = timestamp = slack = ''
            time = data.get('time')
            timemode = time[0] if time and len(time) == 2 else ''
            if timemode == 'days':
                days = time[1]
            elif timemode == 'timestamp':
                timestamp, slack = time[1].split('|')

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
                'DESC'
            )
            query.execute()
            (
                total_time,
                total_sent,
                total_received
            ) = query.make_stats()
            context.update({
                'result': query.result,
                'total_time': total_time,
                'total_sent': total_sent,
                'total_received': total_received,
            })
        else:
            context['errors'] = form.errors
    else:
        form = AccountLogSearchForm()

    context.update({
        'title': TITLE,
        'navpath': NAVPATH,
        'form': form,
        'acctsearch': True
    })

    return render_to_response('radius/account_log.html', context,
                              context_instance=RequestContext(request))
