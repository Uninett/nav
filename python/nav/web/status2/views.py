#
# Copyright (C) 2014, 2015 Uninett AS
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
"""NAV status app views"""

import base64
import datetime
import logging
import pickle

from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse, Http404
from django.urls import reverse

from nav.maintengine import check_devices_on_maintenance
from nav.event2 import EventFactory
from nav.models.event import AlertHistory
from nav.models.manage import Netbox, NetboxEntity, Module
from nav.models.msgmaint import MaintenanceTask, MaintenanceComponent
from nav.models.fields import INFINITY
from nav.web.auth.utils import get_account, set_account
from . import forms, STATELESS_THRESHOLD

_logger = logging.getLogger(__name__)

device_event = EventFactory('ipdevpoll', 'eventEngine', 'deviceState')


class StatusView(View):
    """Generic Status view"""

    def get_status_preferences(self):
        """Gets the status preferences for the user on the request"""
        account = get_account(self.request)
        preferences = account.preferences.get(account.PREFERENCE_KEY_STATUS)
        if preferences:
            try:
                if preferences.startswith("b'") and preferences.endswith("'"):
                    # Status filter was incorrectly saved as a string representation of
                    # bytes without being decoded ("b'1234", instead of "1234")
                    preferences = preferences[2:-1]
                    account.preferences[account.PREFERENCE_KEY_STATUS] = preferences
                    account.save()
                data = base64.b64decode(preferences)
                set_account(self.request, account, cycle_session_id=False)
                return pickle.loads(data)
            except Exception:  # noqa: BLE001 - maybe an old, none-base64 pickle
                _logger.exception(
                    "Ignoring potential legacy status preferences for user %s",
                    account.login,
                )
                return self.set_default_parameters({})

    @staticmethod
    def set_default_parameters(parameters):
        """Populates the parameters with the default stateless threshold."""
        if 'stateless_threshold' not in parameters:
            parameters.update({'stateless_threshold': STATELESS_THRESHOLD})

    def get_permits(self):
        """Get the permits relevant for the page for the account"""
        account = get_account(self.request)
        can_acknowledge_alerts = account.has_perm('can_acknowledge_alert', '')
        can_clear_alerts = account.has_perm('can_clear_alert', '')
        can_put_on_maintenance = account.has_perm(
            'web_access', reverse('maintenance-new')
        )
        return {
            'any': any(
                [can_acknowledge_alerts, can_clear_alerts, can_put_on_maintenance]
            ),
            'can_acknowledge_alerts': can_acknowledge_alerts,
            'can_clear_alerts': can_clear_alerts,
            'can_put_on_maintenance': can_put_on_maintenance,
        }

    def get(self, request):
        """Produces a list view of AlertHistory entries"""
        if request.GET:
            parameters = request.GET.copy()
            self.set_default_parameters(parameters)
            form = forms.StatusPanelForm(parameters)
        else:
            form = forms.StatusPanelForm(self.get_status_preferences())

        return render(
            request,
            'status2/status.html',
            {
                'title': 'NAV - Status',
                'navpath': [('Home', '/'), ('Status', '')],
                'form': form,
                'permits': self.get_permits(),
            },
        )


def save_status_preferences(request):
    """Saves the status preferences for the logged in user."""

    form = forms.StatusPanelForm(request.POST)
    if form.is_valid():
        account = get_account(request)
        datastring = base64.b64encode(pickle.dumps(form.cleaned_data)).decode()
        account.preferences[account.PREFERENCE_KEY_STATUS] = datastring
        account.save()
        set_account(request, account, cycle_session_id=False)
        return HttpResponse()
    else:
        return HttpResponse('Form was not valid', status=400)


def get_alerts_from_request(request, event_type_filter=None):
    """Gets all the alerts from the request by looking for a list of ids

    If no alerts are found, raises 404

    :param event_type_filter: event type ids to filter on
    :type event_type_filter: list[string]
    """
    alerts = AlertHistory.objects.filter(pk__in=request.POST.getlist('id[]'))
    if event_type_filter is not None:
        alerts = [a for a in alerts if a.event_type.id in event_type_filter]
    if not alerts:
        raise Http404
    return alerts


def handle_resolve_alerts(request):
    """Handles a resolve alerts request"""
    if request.method == 'POST':
        resolve_alerts(get_alerts_from_request(request))
        return HttpResponse()
    else:
        return HttpResponse(status=400)


def resolve_alerts(alerts):
    """Resolves alerts by setting end_time of the alerts to now"""
    for alert in alerts:
        alert.end_time = datetime.datetime.now()
        alert.save()


def acknowledge_alert(request):
    """Acknowledges all alerts and gives them the same comment"""
    if request.method == 'POST':
        alerts = get_alerts_from_request(request)
        comment = request.POST.get('comment')
        account = get_account(request)
        for alert in alerts:
            alert.acknowledge(account, comment)
        return HttpResponse()
    else:
        return HttpResponse('Wrong request type', status=400)


def put_on_maintenance(request):
    """Puts the subject of the alerts on maintenance"""
    if request.method == 'POST':
        account = get_account(request)
        alerts = get_alerts_from_request(request)
        netboxes = Netbox.objects.filter(pk__in=[x.netbox_id for x in alerts])
        if not netboxes:
            return HttpResponse("No netboxes found", status=404)

        default_descr = (
            "On maintenance till up again; set from status page by " + account.login
        )
        description = request.POST.get('description') or default_descr
        candidates = [n for n in netboxes if not is_maintenance_task_posted(n)]
        if candidates:
            add_maintenance_task(account, candidates, description)
            check_devices_on_maintenance()
        return HttpResponse(status=200)
    else:
        return HttpResponse('Wrong request type', status=400)


def delete_module_or_chassis(request):
    """Deletes a module or chassis from the database

    This is done by looking up the device from the alerthistory ids in the
    request, and deleting all netbox entities and modules corresponding to that
    device.
    """
    accepted_event_types = ['moduleState', 'chassisState']

    if request.method == 'POST':
        alerts = get_alerts_from_request(
            request, event_type_filter=accepted_event_types
        )
        module_ids = []
        entity_ids = []
        notify_events = []

        for alert in alerts:
            if alert.event_type.pk == 'moduleState':
                module_ids.append(alert.subid)
                notify_events.append(
                    (alert.device, alert.netbox, "deviceDeletedModule")
                )
            elif alert.event_type.pk == 'chassisState':
                entity_ids.append(alert.subid)
                notify_events.append(
                    (alert.device, alert.netbox, "deviceDeletedChassis")
                )

        Module.objects.filter(pk__in=module_ids).delete()
        NetboxEntity.objects.filter(pk__in=entity_ids).delete()
        resolve_alerts(alerts)

        for device, netbox, alert_type in notify_events:
            device_event.notify(
                device=device,
                netbox=netbox,
                alert_type=alert_type,
            ).save()

        return HttpResponse()

    return HttpResponse('Wrong request type', status=400)


def is_maintenance_task_posted(netbox):
    """Verify that a maintenance task for this netbox is not already posted"""
    return MaintenanceComponent.objects.filter(
        key='netbox',
        value=str(netbox.id),
        maintenance_task__state=MaintenanceTask.STATE_ACTIVE,
        maintenance_task__end_time=datetime.datetime.max,
    ).count()


def add_maintenance_task(owner, netboxes, description=""):
    """Add a maintenance task with a component for each netbox"""
    if not netboxes:
        return

    task = MaintenanceTask(
        start_time=datetime.datetime.now(),
        end_time=INFINITY,
        description=description,
        author=owner.login,
        state=MaintenanceTask.STATE_SCHEDULED,
    )
    task.save()

    for netbox in netboxes:
        component = MaintenanceComponent(
            maintenance_task=task, key='netbox', value='%d' % netbox.id
        )
        component.save()
