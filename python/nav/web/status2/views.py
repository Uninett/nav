#
# Copyright (C) 2014, 2015 UNINETT
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
"""NAV status app views"""
import datetime
import pickle

from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.views.generic import View
from django.db.models import Q
from django.http import HttpResponse

from rest_framework import viewsets, filters
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from nav.maintengine import check_devices_on_maintenance
from nav.models.event import AlertHistory
from nav.models.manage import Netbox
from nav.models.msgmaint import MaintenanceTask, MaintenanceComponent
from nav.models.profiles import AccountProperty
from nav.models.fields import UNRESOLVED, INFINITY
from . import forms, STATELESS_THRESHOLD, STATUS_PREFERENCE_PROPERTY


class StatusView(View):
    """Generic Status view"""

    def get_status_preferences(self):
        try:
            status_property = self.request.account.properties.get(
                property=STATUS_PREFERENCE_PROPERTY)
        except AccountProperty.DoesNotExist:
            pass
        else:
            return pickle.loads(status_property.value)

    @staticmethod
    def set_default_parameters(parameters):
        if 'stateless_threshold' not in parameters:
            parameters.update({'stateless_threshold': STATELESS_THRESHOLD})

    def get_permits(self):
        """Get the permits relevant for the page for the account"""
        account = self.request.account
        can_acknowledge_alerts = account.has_perm('can_acknowledge_alert', '')
        can_clear_alerts = account.has_perm('can_clear_alert', '')
        can_put_on_maintenance = account.has_perm(
            'web_access', reverse('maintenance-new'))
        return {
            'any': any([can_acknowledge_alerts, can_clear_alerts,
                        can_put_on_maintenance]),
            'can_acknowledge_alerts': can_acknowledge_alerts,
            'can_clear_alerts': can_clear_alerts,
            'can_put_on_maintenance': can_put_on_maintenance
        }

    def get(self, request):
        """Produces a list view of AlertHistory entries"""
        if request.GET.values():
            parameters = request.GET.copy()
            self.set_default_parameters(parameters)
            form = forms.StatusPanelForm(parameters)
        else:
            form = forms.StatusPanelForm(self.get_status_preferences())

        return render_to_response(
            'status2/status.html',
            {
                'title': 'NAV - Status',
                'navpath': [('Home', '/'), ('Status', '')],
                'form': form,
                'permits': self.get_permits()
            },
            RequestContext(request)
        )


def save_status_preferences(request):
    """Saves the status preferences for the logged in user."""

    form = forms.StatusPanelForm(request.POST)
    if form.is_valid():
        try:
            status_property = request.account.properties.get(
                property=STATUS_PREFERENCE_PROPERTY)
        except AccountProperty.DoesNotExist:
            status_property = AccountProperty(
                account=request.account, property=STATUS_PREFERENCE_PROPERTY)

        status_property.value = pickle.dumps(form.cleaned_data)
        status_property.save()
        return HttpResponse()
    else:
        return HttpResponse('Form was not valid', status=400)


def get_alerts_from_request(request):
    return AlertHistory.objects.filter(pk__in=request.POST.getlist('id[]'))


def resolve_alerts(request):
    """Resolves alerts by setting end_time of the alerts to now"""
    if request.method == 'POST':
        alerts = get_alerts_from_request(request)
        if not alerts:
            return HttpResponse(status=404)
        for alert in alerts:
            alert.end_time = datetime.datetime.now()
            alert.save()
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)


def acknowledge_alert(request):
    """Acknowledges all alerts and gives them the same comment"""
    if request.method == 'POST':
        alerts = get_alerts_from_request(request)
        if not alerts:
            return HttpResponse("No alerts found", status=404)

        comment = request.POST.get('comment')
        for alert in alerts:
            alert.acknowledge(request.account, comment)
        return HttpResponse()
    else:
        return HttpResponse('Wrong request type', status=400)


def put_on_maintenance(request):
    """Puts the subject of the alerts on maintenance"""
    if request.method == 'POST':
        alerts = get_alerts_from_request(request)
        netboxes = Netbox.objects.filter(pk__in=[x.netbox_id for x in alerts])
        if not netboxes:
            return HttpResponse("No netboxes found", status=404)

        default_descr = "On maintenance till up again; set from status page " \
                        "by " + request.account.login
        description = request.POST.get('description') or default_descr
        candidates = [n for n in netboxes if not is_maintenance_task_posted(n)]
        if len(candidates):
            add_maintenance_task(request.account, candidates, description)
            check_devices_on_maintenance()
        return HttpResponse(status=200)
    else:
        return HttpResponse('Wrong request type', status=400)


def is_maintenance_task_posted(netbox):
    """Verify that a maintenance task for this netbox is not already posted"""
    return MaintenanceComponent.objects.filter(
        key='netbox',
        value=str(netbox.id),
        maintenance_task__state=MaintenanceTask.STATE_ACTIVE,
        maintenance_task__end_time=datetime.datetime.max).count()


def add_maintenance_task(owner, netboxes, description=""):
    """Add a maintenance task with a component for each netbox"""
    if not len(netboxes):
        return

    task = MaintenanceTask(
        start_time=datetime.datetime.now(),
        end_time=INFINITY,
        description=description,
        author=owner.login,
        state=MaintenanceTask.STATE_SCHEDULED
    )
    task.save()

    for netbox in netboxes:
        component = MaintenanceComponent(
            maintenance_task=task,
            key='netbox',
            value='%d' % netbox.id
        )
        component.save()

