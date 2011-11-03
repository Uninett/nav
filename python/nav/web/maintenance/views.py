#
# Copyright (C) 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import nav.maintenance

from datetime import datetime

from django.core.urlresolvers import reverse
from django.db.models import Count
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404

from nav.django.utils import get_account
from nav.models.msgmaint import MaintenanceTask, MaintenanceComponent
from nav.web.message import new_message, Messages

from nav.web.maintenance.utils import task_components

def active(request):
    tasks = MaintenanceTask.objects.filter(
        start_time__lt=datetime.now(),
        end_time__gt=datetime.now()
    ).annotate(component_count=Count('maintenancecomponent'))
    return render_to_response(
        'maintenance/list.html',
        {
            'active': {'active': True},
            'tasks': tasks,
        },
        RequestContext(request)
    )

def planned(request):
    tasks = nav.maintenance.getTasks('maint_start > now() AND maint_end > NOW()')
    tasks = MaintenanceTask.objects.filter(
        start_time__gt=datetime.now(),
        end_time__gt=datetime.now()
    ).annotate(component_count=Count('maintenancecomponent'))
    return render_to_response(
        'maintenance/list.html',
        {
            'active': {'planned': True},
            'tasks': tasks,
        },
        RequestContext(request)
    )

def historic(request):
    tasks = MaintenanceTask.objects.filter(
        end_time__lt=datetime.now()
    ).annotate(component_count=Count('maintenancecomponent'))
    return render_to_response(
        'maintenance/list.html',
        {
            'active': {'historic': True},
            'tasks': tasks,
        },
        RequestContext(request)
    )

def view(request, task_id):
    tasks = nav.maintenance.getTask(task_id)
    if not tasks:
        raise Http404()
    task = tasks[0]
    components = task_components(task)
    return render_to_response(
        'maintenance/details.html',
        {
            'task': task,
            'components': components,
        },
        RequestContext(request)
    )

def cancel(request, task_id):
    account = get_account(request)
    if account.is_default_account():
        #FIXME redirect
        raise Exception("Oh noes")

    task = get_object_or_404(MaintenanceTask, pk=task_id)
    if request.method == 'POST':
        task.state = 'canceled'
        task.save()
        new_message(request._req,
            "This task is now cancelled.", Messages.SUCCESS)
        url = reverse('maintenance-view', args=[task_id])
        return HttpResponseRedirect(reverse('maintenance-view', args=[task_id]))
    else:
        return render_to_response(
            'maintenance/cancel.html',
            {
                'task': task,
            },
            RequestContext(request)
        )
