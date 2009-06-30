# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Status sections"""

from datetime import datetime

from django.db.models import Q
from django.core.urlresolvers import reverse

from nav.models.profiles import StatusPreference
from nav.models.event import AlertHistory, AlertType, AlertHistoryVariable
from nav.models.manage import Netbox

from nav.web.status.filters import OrganizationFilter, CategoryFilter, \
    StateFilter, ServiceFilter

MAINTENANCE_STATE = 'maintenanceState'
BOX_STATE = 'boxState'

def get_user_sections(account):
    sections = []
    preferences = StatusPreference.objects.filter(
        account=account
    ).order_by('position')

    for pref in preferences:
        if pref.type == StatusPreference.SECTION_NETBOX:
            sections.append(NetboxSection(
                name=pref.name,
                organizations=pref.organizations.values_list('id', flat=True),
                categories=pref.categories.values_list('id', flat=True),
                states=pref.states,
            ))
        elif pref.type == StatusPreference.SECTION_NETBOX_MAINTENANCE:
            sections.append(NetboxMaintenanceSection(
                name=pref.name,
                organizations=pref.organizations.values_list('id', flat=True),
                categories=pref.categories.values_list('id', flat=True),
                states=pref.states,
            ))
        elif pref.type == StatusPreference.SECTION_MODULE:
            pass
        elif pref.type == StatusPreference.SECTION_SERVICE:
            pass

    return sections

class _Section(object):
    '''Base class for sections.

    Attributes:
        columns - tuples of the wanted columns. First part gives the displayed
                  name of the column, while the second defines the field that
                  are looked up in the database.

        history - the query used to look up the history
    '''
    columns = []
    history = None

    def __init__(self, **kwargs):
        self.name = kwargs.pop('name')

class NetboxSection(_Section):
    columns =  [
        'Sysname',
        'IP',
        'Down since',
        'Downtime',
    ]

    def __init__(self, **kwargs):
        self.organizations = kwargs.pop('organizations')
        self.categories = kwargs.pop('categories')
        self.states = kwargs.pop('states').split(',')

        super(NetboxSection, self).__init__(**kwargs)
        self.history = self._history()

    def _history(self):
        maintenance = self._maintenance()
        alert_types = self._alerttype()

        netbox_history = AlertHistory.objects.select_related(
            'netbox'
        ).filter(
            ~Q(netbox__in=maintenance),
            Q(netbox__up='n') | Q(netbox__up='s'),
            alert_type__in=alert_types,
            end_time__gt=datetime.max,
            netbox__category__in=self.categories,
            netbox__organization__in=self.organizations,
        ).extra(
            select={'downtime': 'NOW() - start_time'}
        ).order_by('-start_time', 'end_time')

        history = []
        for h in netbox_history:
            row = (
                (
                    h.netbox.sysname,
                    reverse('ipdevinfo-details-by-name', args=[h.netbox.sysname])
                ),
                (h.netbox.ip, None),
                (h.start_time, None),
                (h.downtime, None),
            )
            history.append(row)
        return history

    def _maintenance(self):
        return AlertHistory.objects.filter(
            event_type=MAINTENANCE_STATE,
            end_time__gt=datetime.max,
        ).values('netbox').query

    def _alerttype(self):
        states = []
        if 'y' in self.states:
            states.append('boxUp')
        if 'n' in self.states:
            states.append('boxDown')
        if 's' in self.states:
            states.append('boxShadow')

        return AlertType.objects.filter(
            event_type__id=BOX_STATE,
            name__in=states
        ).values('pk').query

class NetboxMaintenanceSection(NetboxSection):
    columns =  [
        'Sysname',
        'IP',
        'Down since',
        'Downtime',
    ]

    def _history(self):
        maintenance = self._maintenance()
        boxes_down = self._boxes_down()

        history = []
        for m in maintenance:
            # Find out if the box is down as well as on maintenance
            down = boxes_down.get(m.alert_history.netbox.id, None)

            if m.alert_history.netbox.up == 'y':
                down_since = 'Up'
                downtime = ''
            else:
                if down:
                   down_since = down['start_time']
                   downtime = down['downtime']
                else:
                    down_since = 'N/A'
                    downtime = 'N/A'

            row = (
                (
                    m.alert_history.netbox.sysname,
                    reverse('ipdevinfo-details-by-name', args=[m.alert_history.netbox.sysname])
                ),
                (m.alert_history.netbox.ip, None),
                (down_since, None),
                (downtime, None),
            )
            history.append(row)
        return history

    def _maintenance(self):
        return AlertHistoryVariable.objects.select_related(
            'alert_history', 'alert_history__netbox'
        ).filter(
            alert_history__netbox__category__in=self.categories,
            alert_history__netbox__organization__in=self.organizations,
            alert_history__netbox__up__in=self.states,
            alert_history__end_time__gt=datetime.max,
            alert_history__event_type=MAINTENANCE_STATE,
            variable='maint_taskid',
        ).order_by('-alert_history__start_time')

    def _boxes_down(self):
        history = AlertHistory.objects.select_related(
            'netbox'
        ).filter(
            end_time__gt=datetime.max,
            event_type=BOX_STATE,
        ).extra(
            select={'downtime': 'NOW() - start_time'}
        ).order_by('-start_time').values(
            'netbox', 'start_time', 'downtime'
        )

        ret = {}
        for h in history:
            ret[h['netbox']] = h
        return ret
