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
"""Status sections.

Used to build up different sections for display.
"""

from datetime import datetime

from django.db.models import Q
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_unicode, smart_str, force_unicode

from nav.models.profiles import StatusPreference, StatusPreferenceCategory, \
    StatusPreferenceOrganization
from nav.models.event import AlertHistory, AlertType, AlertHistoryVariable
from nav.models.manage import Netbox, Module, Category, Organization

from nav.web import serviceHelper

MAINTENANCE_STATE = 'maintenanceState'
BOX_STATE = 'boxState'
SERVICE_STATE = 'serviceState'
MODULE_STATE = 'moduleState'
THRESHOLD_STATE = 'thresholdState'


def get_user_sections(account):
    '''Fetches all status sections for account in one swoop.
    '''
    # Dispatch table
    dtable = {
        StatusPreference.SECTION_NETBOX: NetboxSection,
        StatusPreference.SECTION_NETBOX_MAINTENANCE: NetboxMaintenanceSection,
        StatusPreference.SECTION_MODULE: ModuleSection,
        StatusPreference.SECTION_SERVICE: ServiceSection,
        StatusPreference.SECTION_SERVICE_MAINTENANCE: ServiceMaintenanceSection,
        StatusPreference.SECTION_THRESHOLD: ThresholdSection,
    }

    sections = []
    preferences = StatusPreference.objects.filter(
        account=account
    ).order_by('position')

    # Pre-fetching all categories and organisations
    all_cats = Category.objects.values_list('pk', flat=True)
    all_orgs = Organization.objects.values_list('pk', flat=True)

    categories = {}
    organizations = {}
    cats = StatusPreferenceCategory.objects.filter(
        statuspreference__in=preferences
    )
    orgs = StatusPreferenceOrganization.objects.filter(
        statuspreference__in=preferences
    )

    # Buld dicts with statuspreference_id as keys.
    for cat in cats:
        if not cat.statuspreference_id in categories:
            categories[cat.statuspreference_id] = []
        categories[cat.statuspreference_id].append(cat.category_id)
    for org in orgs:
        if not org.statuspreference_id in organizations:
            organizations[org.statuspreference_id] = []
        organizations[org.statuspreference_id].append(org.organization_id)

    # Add pre fetched categories and organisations to section preferences.
    # Adds all categories and organisations if nothing is found in database.
    for pref in preferences:
        pref.fetched_categories = categories.get(pref.id, all_cats)
        pref.fetched_organizations = organizations.get(pref.id, all_orgs)

    for pref in preferences:
        section = dtable[pref.type](prefs=pref)
        section.fetch_history()
        sections.append(section)

    return sections

class _Section(object):
    '''Base class for sections.

    Attributes:
        columns - tuples of the wanted columns. First part gives the displayed
                  name of the column, while the second defines the field that
                  are looked up in the database.

        history - the query used to look up the history

        type_title - readable type name of this section

        devicehistory_type - used in links to devicehistory
    '''
    columns = []
    history = []
    type_title = ''
    devicehistory_type = ''

    def __init__(self, prefs=None):
        self.prefs = prefs
        self.categories = self.prefs.fetched_categories
        self.organizations = self.prefs.fetched_organizations
        self.states = self.prefs.states.split(',')

        for key, title in StatusPreference.SECTION_CHOICES:
            if self.prefs.type == key:
                self.type_title = title
                break

    def fetch_history(self):
        self.history = []

    def devicehistory_url(self):
        netboxes = Netbox.objects.filter(
            category__in=self.categories,
            organization__in=self.organizations,
        ).values('id')
        url = reverse('devicehistory-view')
        url += "?type=%s" % self.devicehistory_type
        url += "&group_by=datetime"
        for n in netboxes:
            url += "&netbox=%s" % n['id']
        return url

class NetboxSection(_Section):
    columns =  [
        'Sysname',
        'IP',
        'Down since',
        'Downtime',
        '',
    ]
    devicehistory_type = 'a_3'

    def fetch_history(self):
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
                (
                    'history',
                    reverse('devicehistory-view') +\
                    '?netbox=%(id)s&type=a_3&group_by=datetime' % {
                        'id': h.netbox.id,
                    }
                ),
            )
            history.append(row)
        self.history = history

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

class NetboxMaintenanceSection(_Section):
    columns =  [
        'Sysname',
        'IP',
        'Down since',
        'Downtime',
        '',
    ]
    devicehistory_type = 'e_maintenanceState'

    def fetch_history(self):
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
                (
                    'history',
                    reverse('devicehistory-view') +\
                    '?netbox=%(id)s&type=e_maintenanceState&group_by=datetime' % {
                        'id': m.alert_history.netbox.id,
                    }
                ),
            )
            history.append(row)
        self.history = history

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

class ServiceSection(_Section):
    columns = [
        'Sysname',
        'Handler',
        'Down since',
        'Downtime',
        '',
    ]
    devicehistory_type = 'e_serviceState'

    def __init__(self, prefs=None):
        super(ServiceSection, self).__init__(prefs=prefs)
        if self.prefs.services:
            self.services = self.prefs.services.split(',')
        else:
            self.services = [s for s in serviceHelper.getCheckers()]

    def fetch_history(self):
        maintenance = AlertHistory.objects.filter(
            end_time__gt=datetime.max,
            event_type=MAINTENANCE_STATE,
        ).values('netbox').query

        services = AlertHistory.objects.select_related(
            'netbox'
        ).filter(
            ~Q(netbox__in=maintenance),
            end_time__gt=datetime.max,
            event_type=SERVICE_STATE,
            netbox__organization__in=self.organizations,
        ).extra(
            select={
                'downtime': 'NOW() - start_time',
                'handler': 'service.handler',
            },
            tables=['service'],
            where=[
                'alerthist.subid = service.serviceid::text',
                'service.handler IN %s',
            ],
            params=[tuple(self.services)]
        )

        history = []
        for s in services:
            row = (
                (
                    s.netbox.sysname,
                    reverse('ipdevinfo-details-by-name', args=[
                        s.netbox.sysname
                    ])
                ),
                (
                    s.handler,
                    reverse('ipdevinfo-service-list-handler', args=[
                        s.handler
                    ])
                ),
                (s.start_time, None),
                (s.downtime, None),
                (
                    'history',
                    reverse('devicehistory-view') +\
                    '?netbox=%(id)s&type=e_serviceState&group_by=datetime' % {
                        'id': s.netbox.id,
                    }
                )
            )
            history.append(row)
        self.history = history

    def devicehistory_url(self):
        # FIXME filter service
        # Service is joined in on the alerthist.subid field, which is not a
        # part of this query. Yay
        netboxes = Netbox.objects.filter(
            organization__in=self.organizations,
        ).values('id')
        url = reverse('devicehistory-view')
        url += "?type=%s" % self.devicehistory_type
        url += "&group_by=datetime"
        for n in netboxes:
            url += "&netbox=%s" % n['id']
        return url

class ServiceMaintenanceSection(ServiceSection):
    devicehistory_type = 'e_maintenanceState'

    def fetch_history(self):
        maintenance = AlertHistoryVariable.objects.select_related(
            'alert_history', 'alert_history__netbox'
        ).filter(
            alert_history__end_time__gt=datetime.max,
            alert_history__event_type=MAINTENANCE_STATE,
            variable='maint_taskid',
        ).extra(
            select={
                'downtime': 'NOW() - start_time',
                'handler': 'service.handler',
                'up': 'service.up',
            },
            tables=['service'],
            where=['subid = serviceid::text'],
        ).order_by('-alert_history__start_time')

        service_history = AlertHistory.objects.filter(
            end_time__gt=datetime.max,
            event_type=SERVICE_STATE,
        ).extra(
            select={'downtime': 'NOW() - start_time'}
        ).values('netbox', 'start_time', 'downtime')

        service_down = {}
        for s in service_history:
            service_down[s['netbox']] = s

        history = []
        for m in maintenance:
            down = service_down.get(m.alert_history.netbox.id, None)

            if m.up == 'y':
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
                (m.handler, reverse('ipdevinfo-service-list-handler', args=[m.handler])),
                (down_since, None),
                (downtime, None),
                (
                    'history',
                    reverse('devicehistory-view') +\
                    '?netbox=%(id)s&type=e_maintenanceState&group_by=datetime' % {
                        'id': m.alert_history.netbox.id,
                    }
                ),
            )
            history.append(row)
        self.history = history

class ModuleSection(_Section):
    columns = [
        'Sysname',
        'IP',
        'Module',
        'Down since',
        'Downtime',
        '',
    ]
    devicehistory_type = 'a_8'

    def fetch_history(self):
        module_history = AlertHistory.objects.select_related(
            'netbox', 'device'
        ).filter(
            end_time__gt=datetime.max,
            event_type=MODULE_STATE,
            alert_type__name='moduleDown',
            netbox__organization__in=self.organizations,
            netbox__category__in=self.categories,
        ).extra(
            select={
                'downtime': 'NOW() - start_time',
                'module_id': 'module.moduleid',
                'module_number': 'module.module',
            },
            tables=['module'],
            where=[
                'alerthist.subid = module.moduleid::text',
                'module.up IN %s',
            ],
            params=[tuple(self.states)]
        ).order_by('-start_time')

        history = []
        for module in module_history:
            row = (
                (
                    module.netbox.sysname,
                    reverse('ipdevinfo-details-by-name', args=[module.netbox.sysname])
                ),
                (module.netbox.ip, None),
                (
                    module.module_number,
                    reverse('ipdevinfo-module-details', args=[
                        module.netbox.sysname,
                        module.module_number
                    ])
                ),
                (module.start_time, None),
                (module.downtime, None),
                (
                    'history',
                    reverse('devicehistory-view') +\
                    '?module=%(id)s&type=a_8&group_by=datetime' % {
                        'id': module.module_id,
                    }
                ),
            )
            history.append(row)
        self.history = history

class ThresholdSection(_Section):
    columns = [
        'Sysname',
        'Description',
        'Exceeded since',
        'Time exceeded',
        '',
    ]
    devicehistory_type = 'a_14'

    def fetch_history(self):
        thresholds = AlertHistory.objects.select_related(
            'netbox'
        ).filter(
            end_time__gt=datetime.max,
            event_type=THRESHOLD_STATE,
            alert_type__name='exceededThreshold',
            netbox__organization__in=self.organizations,
            netbox__category__in=self.categories,
        ).extra(
            select={
                'downtime': 'NOW() - start_time',
                'rrd_description': 'rrd_datasource.descr',
                'rrd_units': 'rrd_datasource.units',
                'rrd_threshold': 'rrd_datasource.threshold',
            },
            tables=['rrd_datasource'],
            where=['subid = rrd_datasource.rrd_datasourceid::text']
        ).order_by('-start_time')

        history = []
        for t in thresholds:
            rrd_description = t.rrd_description
            if not rrd_description:
                rrd_description = 'Unknown datasource'
            description = '%(descr)s exceeded %(threshold)s%(units)s' % {
                'descr': rrd_description,
                'threshold': t.rrd_threshold,
                'units': t.rrd_units,
            }

            row = (
                (
                    t.netbox.sysname,
                    reverse('ipdevinfo-details-by-name', args=[t.netbox.sysname])
                ),
                (description, None),
                (t.start_time, None),
                (t.downtime, None),
                (
                    'history',
                    reverse('devicehistory-view') +\
                    '?netbox=%(id)s&type=a_14&group_by=datetime' % {
                        'id': t.netbox.id,
                    }
                ),
            )
            history.append(row)
        self.history = history
