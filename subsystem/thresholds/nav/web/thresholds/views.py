# -*- coding: utf-8 -*-
#
# Copyright 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#

__copyright__ = "Copyright 2011 UNINETT AS"
__license__ = "GPL"
__author__ = "Trond Kandal <Trond.Kandal@ntnu.no>"
__id__ = "$Id$"

import logging

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, Context
from django.shortcuts import render_to_response
from nav.django.utils import get_account

from nav.models.manage import Netbox, Interface
from nav.models.rrd import RrdFile, RrdDataSource
from nav.web.thresholds.utils import *

NAVBAR = [('Home', '/'), ('Manage thresholds', None)]
DEFAULT_VALUES = {'title': "Manage thresholds", 'navpath': NAVBAR}

logger = logging.getLogger("nav.web.thresholds")

def render_base_page(request, info_dict):
    return render_to_response(
        'thresholds/base.html',
        info_dict,
        RequestContext(request)
        )

def index(request):
    info_dict = populate_info_dict(get_account(request))
    return render_base_page(request, info_dict)
    
def show_interface(request, interfaceid):
    if not is_legal_interfaceid(interfaceid):
        msgs = ['Illegal interfaceid',]
        info_dict = populate_info_dict(get_account(request),
                                        messages=msgs)
        return render_base_page(request, info_dict)
    return render_show_interface(request, interfaceid)
 
def render_show_interface(req, interfaceid, messages=None):
    interface = get_interface(interfaceid)
    if not interface:
        msgs = ['Illegal interfaceid',]
        info_dict = populate_info_dict(get_account(req), messages=msgs)
        return render_base_page(request, info_dict)

    rrd_files = get_rrdfiles_objects(interface)
    if not rrd_files:
        msgs = ['Illegal interfaceid',]
        info_dict = populate_info_dict(get_account(req), messages=msgs)
        return render_base_page(request, info_dict)

    rrd_data_sources = get_rrd_data_sources(rrd_files)
    info_dict = None
    if rrd_data_sources:
        info_dict = populate_info_dict(get_account(req),
                                    interface=interface,
                                    rrd_data_sources=rrd_data_sources)
        req._req.session['interface_id'] = interfaceid
        req._req.session['rrd_data_sources'] = []
        for source in rrd_data_sources:
            req._req.session['rrd_data_sources'].append(source.id)
    else:
        info_dict = populate_info_dict(get_account(req),
                                        interface=interface)
    if messages:
        info_dict.update( {'messages': messages})

    return render_to_response(
        'thresholds/showinterface.html',
        info_dict,
        RequestContext(req)
        )


def update_threshold(request):
    interfaceid = request._req.session.get('interface_id', None)
    if not is_legal_interfaceid(interfaceid):
        msgs = ['Illegal interfaceid',]
        info_dict = populate_info_dict(get_account(request),
                                        messages=msgs)
        return render_base_page(request, info_dict)
    
    # Only POST is permitted
    if request.method != 'POST':
        msgs = ['illegal request',]
        return render_show_interface(request,
                        interfaceid,
                        messages=msgs)
    # do the real work
    datasourceid = request.POST.get('datasourceid', None)
    operator = request.POST.get('operator', None)
    threshold = request.POST.get('threshold', None)

    if not is_legal_datasourceid(request, datasourceid):
        msgs = ['Illegal identifier',]
        return render_show_interface(request,
                        interfaceid,
                        messages=msgs)

    if not is_legal_threshold(threshold):
        msgs = ['Illegal threshold',]
        return render_show_interface(request,
                        interfaceid,
                        messages=msgs)

    if not is_legal_operator(operator):
        msgs = ['Illegal operator',]
        return render_show_interface(request,
                        interfaceid,
                        messages=msgs)

    datasourceid = int(datasourceid.strip())
    to_update = get_rrd_data_source(datasourceid)
    if not to_update:
        msgs = ['Illegal identifier',]
        return render_show_interface(request,
                        interfaceid,
                        messages=msgs)

    to_update.threshold = threshold.strip()
    to_update.delimiter = get_operator(operator)
    to_update.max = str(THRESHOLD_MAX)
    try :
        to_update.save()
    except Exception, e:
        logger.error(e)
        msgs = [e,]
        render_show_interface(request, interfaceid,
                                messages=msgs)
    return HttpResponseRedirect('/thresholds/interfaceid=%s' % interfaceid)
            
def populate_info_dict(account, messages=None, interface=None, rrd_data_sources=None):
    info_dict = {'account' : account }
    if messages:
        info_dict['messages'] = messages
    if interface:
        info_dict['interface'] = interface
    if rrd_data_sources:
        info_dict['rrd_data_sources'] = rrd_data_sources
    info_dict.update(DEFAULT_VALUES)
    return info_dict
