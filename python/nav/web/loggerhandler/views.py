# -*- coding: UTF-8 -*-
#
# Copyright (C) 2011 UNINETT AS
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
"""macwatch view definitions"""
import copy

import logging
from django.db.models.aggregates import Count
import os
import datetime
from ConfigParser import ConfigParser

from django.http import HttpResponseRedirect, HttpResponseForbidden, \
    HttpResponse, QueryDict
from django.template import RequestContext
#from django.template import Context
from django.shortcuts import render_to_response

import nav
from nav.django.templatetags.info import register

from nav.django.utils import get_account

from nav.models.logger import LogMessage
from nav.models.logger import ErrorError
from nav.models.logger import MessageView
from nav.web.loggerhandler.forms import LoggerSearchForm, LoggerGroupSearchForm

from nav.web.loggerhandler.utils import DbAccess
from nav.web.loggerhandler.utils import ParamUtil


NAVBAR = [('Home', '/'), ('Syslog Analyzer', None)]
DEFAULT_VALUES = {'title': "Syslog Analyzer", 'navpath': NAVBAR}

DATEFORMAT = "%Y-%m-%d %H:%M:%S"

logger = logging.getLogger("nav.web.loggerhandler")


def _get_basic_info_dict(db_access, param_util):
    """
    Get all default parameters for view.
    """
    links = QueryDict("").copy()
    error_list = []
    tfrom = param_util.get_time_from()
    if tfrom:
        links.update({'tfrom': tfrom.strftime(DATEFORMAT)})
    else:
        error_list.append('Illegal from date (YYYY-MM-DD hh:mm:ss).')
    tto = param_util.get_time_to()
    if tto:
        links.update({'tto': tto.strftime(DATEFORMAT)})
    else:
        error_list.append('Illegal to date (YYYY-MM-DD hh:mm:ss).')
    priority =  param_util.get_priority()
    if priority:
        links.update({'priority': priority})
    type_param = param_util.get_type()
    if type_param:
        links.update({'type': type_param})
    origin = param_util.get_origin()
    if origin:
        links.update({'origin': origin})
    category = param_util.get_category()
    if category:
        links.update({'category': category})

    context = {'priority': param_util.get_priority(),
                 'origin': origin,
                 'originid': db_access.get_origin2originid().get(origin,
                                                                None),
                 'category': param_util.get_category(),
                 'type': type_param,
                 'typeid': db_access.get_type2typeid().get(type_param, None),
                 'tto': param_util.get_time_to(),
                 'tfrom': param_util.get_time_from(),
                 'priorities': db_access.get_priorities(),
                 'types': db_access.get_types(),
                 'categories': db_access.get_categories(),
                 'origins': db_access.get_origins(),
                 'origindict':  db_access.get_originid2origin(),
                 'typedict': db_access.get_typeid2type(),
                 'link': links.urlencode(),
                 'error_list': error_list,
                 }
    log = param_util.get_log()
    if log:
        context['log'] = log
    context.update(DEFAULT_VALUES)
    return context

def handle_search(request, searchform):
    account = get_account(request)
    if not account:
        return HttpResponseForbidden("You must be logged in to access this resource")

    results = []
    aggregates = {}

    if len(request.GET.keys()) > 0:
        form = searchform(request.GET)
        if form.is_valid():

            results = LogMessage.objects.filter(time__gte=form.cleaned_data['timestamp_from'], time__lte=form.cleaned_data['timestamp_to']).select_related()
            if form.cleaned_data['priority']:
                results = results.filter(newpriority__in=form.cleaned_data['priority'])
            if form.cleaned_data["message_type"]:
                results = results.filter(type__in=form.cleaned_data['message_type'])
            if form.cleaned_data["category"]:
                results = results.filter(category__in=form.cleaned_data['category'])
            if form.cleaned_data["origin"]:
                results = results.filter(origin__in=form.cleaned_data['origin'])



            priorities = results.values('newpriority__keyword').annotate(sum=Count('newpriority__keyword'))
            priorities_headers = ['Priority']
            message_types = results.values('type__facility', 'type__priority__keyword', 'type__mnemonic').annotate(sum=Count('type'))
            message_types_headers = ['Facility', 'Priority', 'State']
            origins = results.values('origin__name').annotate(sum=Count('origin__name'))
            origins_headers = ['Prefix origin']

            aggregates.update({'priorities' : { 'values': priorities, 'headers': priorities_headers, 'colspan': 1} })
            aggregates.update({'message_type': { 'values': message_types, 'headers': message_types_headers, 'colspan': 3 }})
            aggregates.update({'origin': { 'values': origins, 'headers': origins_headers, 'colspan': 1 }})

    else:
        form = searchform(initial={
            'timestamp_from': (datetime.datetime.now() -
                               datetime.timedelta(days=1)),
            'timestamp_to': datetime.datetime.now()
        })

    context =  {
        'form': form,
        'log_messages': results,
        'aggregates': aggregates,
        }

    return render_to_response('loggerhandler/index.html',
        context,
        RequestContext(request))

def index(request):
    return direct_search(request)

def direct_search(request):
    return handle_search(request, LoggerSearchForm)

def group_search(request):
    return handle_search(request, LoggerGroupSearchForm)



def statistics_reponse(request, db_access=None, param_util=None):
    account = get_account(request)
    if not account:
        return HttpResponseRedirect('/')
    if not db_access:
        db_access = DbAccess()
    if not param_util:
        param_util = ParamUtil(request, db_access)

    info_dict = _get_basic_info_dict(db_access, param_util)
    tfrom_param = info_dict.get('tfrom', None)
    tto_param = info_dict.get('tto', None)
    priority_param = info_dict.get('priority', None)
    type_param = info_dict.get('type', None)
    origin_param = info_dict.get('origin', None)
    category_param = info_dict.get('category', None)

    return render_to_response('loggerhandler/index.html',
                                info_dict,
                                RequestContext(request))

def log_response(request, db_access=None, param_util=None):
    account = get_account(request)
    if not account:
        return HttpResponseRedirect('/')
    if not db_access:
        db_access = DbAccess()
    if not param_util:
        param_util = ParamUtil(request, db_access)
    context = _get_basic_info_dict(db_access, param_util)

    type_param = context.get('type', None)
    origin_param = context.get('origin', None)
    tfrom_param = context.get('tfrom', None)
    tto_param = context.get('tto', None)
    priority_param = context.get('priority', None)
    
    query = None
    if type_param:
        query = LogMessage.objects.filter(type__type=type_param)
    if origin_param:
        if not query:
            query = LogMessage.objects.filter(origin__origin=origin_param)
        else:
            query = query.filter(origin__origin=origin_param)
    if tfrom_param:
        if not query:
            query = LogMessage.objects.filter(time__gte=tfrom_param)
        else:
            query = query.filter(time__gte=tfrom_param)
    if tto_param:
        if not query:
            query = LogMessage.objects.filter(time__lte=tto_param)
        else:
            query = query.filter(time__lte=tto_param)
    if priority_param:
        if not query:
            query = LogMessage.objects.filter(
                                    newpriority__priority=priority_param)
        else:
            query = query.filter(newpriority__priority=priority_param)
    if not query:
        query = LogMessage.objects.all().order_by('-time')
    else:
        query = query.order_by('-time')
    
    # Hit the database
    log_messages = query
    update_dict = {'log_messages': log_messages,
                   'tfrom': tfrom_param.strftime(DATEFORMAT),
                   'tto': tto_param.strftime(DATEFORMAT),
                   'log_mode': True
                  }
    return render_to_response('loggerhandler/index.html',
                                context,
                                RequestContext(request))
    
def statistics_response(request, db_access=None, param_util=None):
    if not db_access:
        db_access = DbAccess()
    if not param_util:
        param_util = ParamUtil(request, db_access)
    info_dict = _get_basic_info_dict(db_access, param_util)

    type_param = info_dict.get('type', None)
    origin_param = info_dict.get('origin', None)
    tfrom_param = info_dict.get('tfrom', None)
    tto_param = info_dict.get('tto', None)
    priority_param = info_dict.get('priority', None)

    return render_to_response('loggerhandler/index.html',
                                info_dict,
                                RequestContext(request))
    
def exceptions_response(request):
    """
    Handler for exception-mode.
    """
    account = get_account(request)
    if not account:
        return HttpResponseRedirect('/')
    db_access = DbAccess()
    param_util = ParamUtil(request, db_access)
    info_dict = _get_basic_info_dict(db_access, param_util)
    config = ConfigParser()
    config.read(os.path.join(nav.path.sysconfdir, 'logger.conf'))
    options = config.options("priorityexceptions")
    excepts = []
    for option in options:
        newpriority = config.get("priorityexceptions", option)
        excepts.append((option, newpriority))
    info_dict['exceptions'] = excepts
    info_dict['exceptions_mode'] = True
    return render_to_response('loggerhandler/frag-exceptions.html',
                                info_dict,
                                RequestContext(request))


def errors_response(request):
    """
    Handler for error-mode.
    """
    account = get_account(request)
    if not account:
        return HttpResponseRedirect('/')
    db_access = DbAccess()
    param_util = ParamUtil(request, db_access)
    info_dict = _get_basic_info_dict(db_access, param_util)
    errs = []
    for err in ErrorError.objects.all():
        errs.append(err.message)
    info_dict['errors'] = errs
    info_dict['errors_count'] = len(errs)
    info_dict['errors_mode'] = True
    return render_to_response('loggerhandler/frag-errors.html',
                                info_dict,
                                RequestContext(request))
