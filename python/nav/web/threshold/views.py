# -*- coding: utf-8 -*-
#
# Copyright 2010 UNINETT AS
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

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Fredrik Skolmli (fredrik.skolmli@uninett.no)"
__id__ = "$Id$"

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, get_list_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.list_detail import object_list

from nav.django.utils import get_account
from nav.models.threshold import Threshold
from nav.models.rrd import RrdFile
from nav.models.manage import Netbox
from nav.web.threshold.forms import ThresholdForm


def threshold_list(request):
    thresholds = Threshold.objects.select_related(depth=2).order_by('descr').order_by('-rrd_file')
    if not 'all' in request.GET.keys():
        result = []
        # Display only those set
        for x in thresholds:
            if x.threshold:
                if len(x.threshold):
                    result.append(x)
    else:
        result = thresholds
    if 'rrd_file' in request.GET.keys():
        result = Threshold.objects.select_related(depth=2).filter(rrd_file=request.GET['rrd_file']).order_by('descr').order_by('-rrd_file')
    elif 'netbox_id' in request.GET.keys():
        result = Threshold.objects.filter(rrd_file=RrdFile.objects.filter(netbox=request.GET['netbox_id'])[0])
    return render_to_response('threshold/start.html', {
    'thresholds': result,
    },
    context_instance=RequestContext(request))

def threshold_edit(request, threshold_id):
    threshold = Threshold.objects.get(pk=threshold_id)
    if len(request.POST.keys()):
        form = ThresholdForm(request.POST, instance=threshold)
        if not form.errors:
            form.save()
    else:
        form = ThresholdForm(instance=threshold)

    return render_to_response('threshold/edit.html', {
    'threshold_form':form,
    'threshold':threshold
    }, context_instance=RequestContext(request))
