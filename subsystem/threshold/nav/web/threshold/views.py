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
# Authors: Fredrik Skolmli <fredrik.skolmli@uninett.no>
#

__copyright__ = "Copyright 2011 UNINETT AS"
__license__ = "GPL"
__author__ = "Fredrik Skolmli <fredrik.skolmli@uninett.no> and Trond Kandal <Trond.Kandal@ntnu.no>"
__id__ = "$Id$"

import logging
import time

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, get_list_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.list_detail import object_list

from nav.django.utils import get_account
from nav.models.rrd import RrdFile, RrdDataSource
from nav.models.manage import Netbox, Interface
from nav.web.threshold.forms import RrdDataSourceForm

NAVBAR = [('Home', '/'), ('Threshold monitor', None)]
DEFAULT_VALUES = {'title': "Threshold monitor", 'navpath': NAVBAR}

logger = logging.getLogger("nav.web.threshold")

def threshold_list(request, all=''):
    logger.error("test")
    thresholds = RrdDataSource.objects.select_related(depth=2).filter(rrd_file__key__iexact='interface').filter(rrd_file__value__isnull=False).order_by('description').order_by('-rrd_file')
    #if not 'all' in request.GET.keys():
    if all != 'all':
        result = []
        # Display only those set
        for x in thresholds:
            if x.threshold:
                if len(x.threshold):
                    result.append(x)
    else:
        result = thresholds
    if 'rrd_file' in request.GET.keys():
        result = RrdDataSource.objects.select_related(depth=2).filter(rrd_file=request.GET['rrd_file']).order_by('descr').order_by('-rrd_file')
    elif 'netbox_id' in request.GET.keys():
        result = RrdDataSource.objects.filter(rrd_file=RrdFile.objects.filter(netbox=request.GET['netbox_id'])[0])
    info_dict = {'thresholds': result}
    info_dict.update(DEFAULT_VALUES)
    return render_to_response(
        'threshold/start.html',
        info_dict,
        RequestContext(request))

def threshold_all(request):
    # pick all sources that have a threshold
    rrd_datasource_list = RrdDataSource.objects.filter(threshold__isnull=False).order_by('rrd_file')
    # attach every datasource to a netbox
    rrd_data_sources= {}
    for rrd_datasource in rrd_datasource_list:
        short_sysname = rrd_datasource.rrd_file.netbox.get_short_sysname()
        if not short_sysname in rrd_data_sources:
            rrd_data_sources[short_sysname] = []
        rrd_data_sources[short_sysname].append(rrd_datasource)

    # the view will present all netbox-nodes in a list,- and the
    # underlying datasources when the nextbox-nodes are expanded.
    before = time.time()
    netboxes = []
    for short_sysname, datasource_list in rrd_data_sources.iteritems():
        netbox = {
            'sysname': short_sysname,
            'sources': datasource_list,
            }
        netboxes.append(netbox)
    logger.error("len = %d" % len(netboxes))
    logger.error("time = %d" % (time.time()-before))
    info_dict = {'netboxes' : netboxes }
    info_dict.update(DEFAULT_VALUES)
    return render_to_response('threshold/listall.html',
        info_dict,
        RequestContext(request))

def threshold_interface(request, interfaceid=None):
    if not interfaceid:
        return HttpResponseRedirect('/threshold/')
    interfaceid = int(interfaceid)
    interface = None
    try :
        interface = Interface.objects.get(pk=interfaceid)
    except Exception, e:
        logger.error(e)
        return HttpResponseRedirect('/threshold/')
    thresholds = RrdDataSource.objects.filter(rrd_file__key__iexact='interface').filter(rrd_file__interface=interfaceid)
    info_dict = {'thresholds': thresholds,}
    info_dict.update(DEFAULT_VALUES)
    return render_to_response('threshold/start.html',
        info_dict,
        RequestContext(request))

def threshold_delete(request, thresholdid=None):
    if not thresholdid:
        return HttpResponseRedirect('/threshold/')
    thresholdid = int(thresholdid)
    threshold = None
    try :
        threshold = RrdDataSource.objects.get(pk=thresholdid)
    except Exception, e:
        logger.error(e)
        return HttpResponseRedirect('/threshold/')
    if len(request.POST.keys()):
        if request.POST.get('submit', '') == 'Yes':
            form = RrdDataSourceForm(request.POST, instance=threshold)
            if not form.errors:
                #form.delete()
                pass
    else:
        info_dict = {'threshold' : threshold}
        info_dict.update(DEFAULT_VALUES)
        return render_to_response('threshold/delete.html',
            info_dict,
            RequestContext(request))
    interfaceid = threshold.rrd_file.interface_id
    url = '/threshold/interface/%d/' % interfaceid
    return HttpResponseRedirect(url)
            
def threshold_edit(request, thresholdid=None):
    if not thresholdid:
        return HttpResponseRedirect('/threshold/')
    threshold = None
    try :
        threshold = RrdDataSource.objects.get(pk=thresholdid)
    except Exception, e:
        logger.error(e)
        return HttpResponseRedirect('/threshold/')
    threshold.max = 100
    if len(request.POST.keys()):
        if request.POST.get('submit', '') == 'Save':
            form = RrdDataSourceForm(request.POST, instance=threshold)
            if not form.errors:
                form.save()
    else:
        form = RrdDataSourceForm(instance=threshold)
        info_dict = {
            'threshold_form': form,
            'threshold': threshold,
            }
        info_dict.update(DEFAULT_VALUES)
        return render_to_response('threshold/edit.html',
            info_dict,
            RequestContext(request))
    url = '/threshold/interface/%d/' % threshold.rrd_file.interface_id
    return HttpResponseRedirect(url)
