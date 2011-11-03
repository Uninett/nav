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

from django.template import RequestContext
from django.shortcuts import render_to_response

from nav.web.maintenance.utils import task_components

def active(request):
    tasks = nav.maintenance.getTasks('maint_start < now() AND maint_end > now()')
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
    return render_to_response(
        'maintenance/list.html',
        {
            'active': {'planned': True},
            'tasks': tasks,
        },
        RequestContext(request)
    )

def historic(request):
    tasks = nav.maintenance.getTasks('maint_end < now()', 'maint_end DESC')
    return render_to_response(
        'maintenance/list.html',
        {
            'active': {'planned': True},
            'tasks': tasks,
        },
        RequestContext(request)
    )

def view(request, task_id):
    tasks = nav.maintenance.getTask(task_id)
    components = task_components(tasks[0])
    return render_to_response(
        'maintenance/details.html',
        {
            'tasks': tasks,
            'components': components,
        },
        RequestContext(request)
    )
