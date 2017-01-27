#
# Copyright (C) 2009, 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Status sections.

Used to build up different sections for display.
"""

from datetime import datetime

from django.db.models import Q
from django.core.urlresolvers import reverse
from nav.metrics.templates import metric_prefix_for_device

from nav.models.profiles import StatusPreference, StatusPreferenceCategory
from nav.models.profiles import StatusPreferenceOrganization
from nav.models.event import AlertHistory, AlertType, AlertHistoryVariable
from nav.models.manage import Netbox, Module, Category, Organization
from nav.models.thresholds import ThresholdRule

from nav.web import servicecheckers

from nav.web.status.forms import SectionForm, NetboxForm
from nav.web.status.forms import NetboxMaintenanceForm, ServiceForm
from nav.web.status.forms import ServiceMaintenanceForm, ModuleForm
from nav.web.status.forms import ThresholdForm, LinkStateForm, SNMPAgentForm

MAINTENANCE_STATE = 'maintenanceState'
BOX_STATE = 'boxState'
SERVICE_STATE = 'serviceState'
MODULE_STATE = 'moduleState'
THRESHOLD_STATE = 'thresholdState'
LINK_STATE = 'linkState'
SNMP_STATE = 'snmpAgentState'
PSU_STATE = 'psuState'


def get_section_model(section_type):
    """Dispatch table"""
    dtable = {
        StatusPreference.SECTION_NETBOX: NetboxSection,
        StatusPreference.SECTION_NETBOX_MAINTENANCE: NetboxMaintenanceSection,
        StatusPreference.SECTION_MODULE: ModuleSection,
        StatusPreference.SECTION_SERVICE: ServiceSection,
        StatusPreference.SECTION_SERVICE_MAINTENANCE: ServiceMaintenanceSection,
        StatusPreference.SECTION_THRESHOLD: ThresholdSection,
        StatusPreference.SECTION_LINKSTATE: LinkStateSection,
        StatusPreference.SECTION_SNMPAGENT: SNMPAgentSection,
        StatusPreference.SECTION_PSU: PSUSection,
    }
    return dtable[section_type]


def get_user_sections(account):
    '''Fetches all status sections for account in one swoop.
    '''
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
        if pref.id in categories:
            pref.fetched_categories = categories[pref.id]
            pref.all_categories = False
        else:
            pref.fetched_categories = all_cats
            pref.all_categories = True
        if pref.id in organizations:
            pref.fetched_organizations = organizations[pref.id]
            pref.all_organizations = False
        else:
            pref.fetched_organizations = all_orgs
            pref.all_organizations = True

    for pref in preferences:
        section_model = get_section_model(pref.type)
        section = section_model(prefs=pref)
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
        """Empty method,- should get overridden in
        sub-classes"""
        self.history = []

    def devicehistory_url(self):
        """Make history urls for this device"""
        url = reverse('devicehistory-view')
        url += "?eventtype=%s" % self.devicehistory_type
        url += "&group_by=datetime"

        if not self.prefs.all_organizations:
            for org in self.organizations:
                url += "&org=%s" % org
        if not self.prefs.all_categories:
            for cat in self.categories:
                url += "&cat=%s" % cat

        # If custom orgs and cats, use AND search
        if not self.prefs.all_categories and not self.prefs.all_organizations:
            url += "&mode=and"

        return url

    @staticmethod
    def form_class():
        """Return the chosen form"""
        return SectionForm

    @staticmethod
    def form_data(status_prefs):
        """Insert data in the form for the view"""
        data = {
            'id': status_prefs.id,
            'name': status_prefs.name,
            'type': status_prefs.type,
            'organizations': list(status_prefs.organizations.values_list(
                    'id', flat=True)) or [''],
        }
        data['categories'] = list(status_prefs.categories.values_list(
                'id', flat=True)) or ['']
        data['states'] = status_prefs.states.split(",")
        return data

    @classmethod
    def form(cls, status_prefs):
        """Get the appropriate form"""
        form_model = cls.form_class()
        data = cls.form_data(status_prefs)
        return form_model(data)


class NetboxSection(_Section):
    columns = [
        'Sysname',
        'IP',
        'Down since',
        'Downtime',
        'History',
        '',
    ]
    devicehistory_type = 'a_boxDown'

    @staticmethod
    def form_class():
        return NetboxForm

    def fetch_history(self):
        maintenance = self._maintenance()
        alert_types = self._alerttype()

        netbox_history = AlertHistory.objects.select_related(
            'netbox'
        ).filter(
            ~Q(netbox__in=maintenance),
            Q(netbox__up='n') | Q(netbox__up='s'),
            alert_type__name__in=alert_types,
            end_time__gte=datetime.max,
            netbox__category__in=self.categories,
            netbox__organization__in=self.organizations,
        ).extra(
            select={'downtime': "date_trunc('second', NOW() - start_time)"}
        ).order_by('-start_time', 'end_time')

        history = []
        for h in netbox_history:
            row = {'netboxid': h.netbox.id,
                   'tabrow': (
                    (
                            h.netbox.sysname,
                        reverse('ipdevinfo-details-by-name',
                            args=[h.netbox.sysname])
                    ),
                    (h.netbox.ip, None),
                    (h.start_time, None),
                    (h.downtime, None),
                    (
                        'history',
                        (reverse('devicehistory-view') +
                         '?netbox=%(id)s&eventtype=a_boxDown&group_by=datetime'
                         % {'id': h.netbox.id})
                    ),
                ),
            }
            history.append(row)
        self.history = history

    def _maintenance(self):
        return AlertHistory.objects.filter(
            event_type=MAINTENANCE_STATE,
            end_time__gte=datetime.max,
            netbox__isnull=False,
        ).values('netbox').query

    def _alerttype(self):
        states = []
        if 'y' in self.states:
            states.append('boxUp')
        if 'n' in self.states:
            states.append('boxDown')
        if 's' in self.states:
            states.append('boxShadow')

        return states


class NetboxMaintenanceSection(_Section):
    columns = [
        'Sysname',
        'IP',
        'Down since',
        'Downtime',
        '',
    ]
    devicehistory_type = 'e_maintenanceState'

    @staticmethod
    def form_class():
        return NetboxMaintenanceForm

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

            row = {'netboxid': m.alert_history.netbox.id,
                   'tabrow': (
                    (
                        m.alert_history.netbox.sysname,
                        reverse('ipdevinfo-details-by-name',
                            args=[m.alert_history.netbox.sysname])
                    ),
                    (m.alert_history.netbox.ip, None),
                    (down_since, None),
                    (downtime, None),
                    (
                        'history',
                        reverse('devicehistory-view') +
                        ('?netbox=%(id)s&eventtype=e_maintenanceState'
                         '&group_by=datetime' %
                         {'id': m.alert_history.netbox.id})
                    ),
                ),
            }
            history.append(row)
        self.history = history

    def _maintenance(self):
        return AlertHistoryVariable.objects.select_related(
            'alert_history', 'alert_history__netbox'
        ).filter(
            alert_history__netbox__category__in=self.categories,
            alert_history__netbox__organization__in=self.organizations,
            alert_history__netbox__up__in=self.states,
            alert_history__end_time__gte=datetime.max,
            alert_history__event_type=MAINTENANCE_STATE,
            variable='maint_taskid',
        ).order_by('-alert_history__start_time')

    def _boxes_down(self):
        history = AlertHistory.objects.select_related(
            'netbox'
        ).filter(
            end_time__gte=datetime.max,
            event_type=BOX_STATE,
        ).extra(
            select={'downtime': "date_trunc('second', NOW() - start_time)"}
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

    @staticmethod
    def form_class():
        return ServiceForm

    @staticmethod
    def form_data(status_prefs):
        data = {
            'id': status_prefs.id,
            'name': status_prefs.name,
            'type': status_prefs.type,
            'organizations': list(status_prefs.organizations.values_list(
                    'id', flat=True)) or [''],
        }
        data['services'] = status_prefs.services.split(",") or ['']
        data['states'] = status_prefs.states.split(",")
        return data

    def __init__(self, prefs=None):
        super(ServiceSection, self).__init__(prefs=prefs)
        if self.prefs.services:
            self.services = self.prefs.services.split(',')
        else:
            self.services = [s for s in servicecheckers.get_checkers()]

    def fetch_history(self):
        maintenance = AlertHistory.objects.filter(
            end_time__gte=datetime.max,
            event_type=MAINTENANCE_STATE,
        ).values('netbox').query

        services = AlertHistory.objects.select_related(
            'netbox'
        ).filter(
            ~Q(netbox__in=maintenance),
            end_time__gte=datetime.max,
            event_type=SERVICE_STATE,
            netbox__organization__in=self.organizations,
        ).extra(
            select={
                'downtime': "date_trunc('second', NOW() - start_time)",
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
            row = {'netboxid': s.netbox.id,
                   'tabrow': (
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
                        reverse('devicehistory-view') +
                        ('?netbox=%(id)s&eventtype=e_serviceState'
                         '&group_by=datetime' %
                         {'id': s.netbox.id})
                    )
                ),
            }
            history.append(row)
        self.history = history

    def devicehistory_url(self):
        url = reverse('devicehistory-view')
        url += "?eventtype=%s" % self.devicehistory_type
        url += "&group_by=datetime"

        if not self.prefs.all_organizations:
            # FIXME filter service
            # Service is joined in on the alerthist.subid field, which is not a
            # part of this query. Yay
            netboxes = Netbox.objects.filter(
                organization__in=self.organizations,
            ).values('id')
            for n in netboxes:
                url += "&netbox=%s" % n['id']
        return url


class ServiceMaintenanceSection(ServiceSection):
    devicehistory_type = 'e_maintenanceState'

    @staticmethod
    def form_class():
        return ServiceMaintenanceForm

    def fetch_history(self):
        maintenance = AlertHistoryVariable.objects.select_related(
            'alert_history', 'alert_history__netbox'
        ).filter(
            alert_history__end_time__gte=datetime.max,
            alert_history__event_type=MAINTENANCE_STATE,
            variable='maint_taskid',
        ).extra(
            select={
                'downtime': "date_trunc('second', NOW() - start_time)",
                'handler': 'service.handler',
                'up': 'service.up',
            },
            tables=['service'],
            where=['subid = serviceid::text'],
        ).order_by('-alert_history__start_time')

        service_history = AlertHistory.objects.filter(
            end_time__gte=datetime.max,
            event_type=SERVICE_STATE,
        ).extra(
            select={'downtime': "date_trunc('second', NOW() - start_time)"}
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

            row = {'netboxid': m.alert_history.netbox.id,
                    'tabrow': (
                    (
                        m.alert_history.netbox.sysname,
                        reverse('ipdevinfo-details-by-name',
                            args=[m.alert_history.netbox.sysname])
                    ),
                    (m.handler, reverse('ipdevinfo-service-list-handler',
                        args=[m.handler])),
                    (down_since, None),
                    (downtime, None),
                    (
                        'history',
                        reverse('devicehistory-view') +
                        ('?netbox=%(id)s&eventtype=e_maintenanceState'
                         '&group_by=datetime' %
                         {'id': m.alert_history.netbox.id})
                    ),
                ),
            }
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
    devicehistory_type = 'a_moduleDown'

    @staticmethod
    def form_class():
        return ModuleForm

    def fetch_history(self, module_history=None):
        module_history = AlertHistory.objects.select_related(
            'netbox', 'device'
        ).filter(
            end_time__gte=datetime.max,
            event_type=MODULE_STATE,
            alert_type__name='moduleDown',
            netbox__organization__in=self.organizations,
            netbox__category__in=self.categories,
        ).extra(
            select={
                'downtime': "date_trunc('second', NOW() - start_time)",
                'module_id': 'module.moduleid',
                'module_name': 'module.name',
            },
            tables=['module'],
            where=[
                'alerthist.deviceid = module.deviceid',
                'module.up IN %s',
            ],
            params=[tuple(self.states)]
        ).order_by('-start_time') if module_history is None else module_history

        history = []
        for module in module_history:
            row = {'netboxid': module.netbox.id,
                   'tabrow': (
                    (
                        module.netbox.sysname,
                        reverse('ipdevinfo-details-by-name',
                            args=[module.netbox.sysname])
                    ),
                    (module.netbox.ip, None),
                    (
                        module.module_name,
                        reverse('ipdevinfo-module-details', args=[
                        module.netbox.sysname,
                        module.module_name
                        ]) if module.module_name else None
                    ),
                    (module.start_time, None),
                    (module.downtime, None),
                    (
                        'history',
                        (reverse('devicehistory-view') +
                         '?module=%(id)s&eventtype=a_moduleDown&'
                         'group_by=datetime' % {'id': module.module_id})
                    ),
                ),
            }
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
    devicehistory_type = 'a_exceededThreshold'

    @staticmethod
    def form_class():
        return ThresholdForm

    @staticmethod
    def form_data(status_prefs):
        data = {
            'id': status_prefs.id,
            'name': status_prefs.name,
            'type': status_prefs.type,
            'organizations': list(status_prefs.organizations.values_list(
                'id', flat=True)) or [''],
            'categories': list(status_prefs.categories.values_list(
                'id', flat=True)) or ['']
        }
        return data

    def fetch_history(self):
        thresholds = AlertHistory.objects.select_related(
            'netbox'
        ).filter(
            end_time__gte=datetime.max,
            event_type=THRESHOLD_STATE,
            alert_type__name='exceededThreshold',
            netbox__organization__in=self.organizations,
            netbox__category__in=self.categories,
        ).extra(
            select={
                'downtime': "date_trunc('second', NOW() - start_time)",
            },
        ).order_by('-start_time')

        history = []
        for alert in thresholds:
            description = self._description_from_alert(alert)
            row = {'netboxid': alert.netbox.id,
                   'tabrow': (
                       (alert.netbox.sysname,
                        reverse('ipdevinfo-details-by-name',
                                args=[alert.netbox.sysname])),
                       (description, None),
                       (alert.start_time, None),
                       (alert.downtime, None),
                       ('history',
                        reverse('devicehistory-view') +
                        '?netbox=%(id)s&eventtype=a_exceededThreshold'
                        '&group_by=datetime' % {
                            'id': alert.netbox.id,
                        }),
                   ),
                   }
            history.append(row)
        self.history = history

    @staticmethod
    def _description_from_alert(alert):
        try:
            ruleid, metric = alert.subid.split(':', 1)
        except ValueError:
            description = None
        else:
            try:
                rule = ThresholdRule.objects.get(id=ruleid)
            except ThresholdRule.DoesNotExist:
                limit = ''
            else:
                limit = rule.alert

            prefix = metric_prefix_for_device(alert.netbox.sysname)
            if metric.startswith(prefix):
                metric = metric[len(prefix)+1:]
            description = "{0} {1}".format(metric, limit)
        return description


class LinkStateSection(_Section):
    columns = [
        'Sysname',
        'IP',
        'Interface',
        'Down since',
        'Downtime',
        'History',
        '',
    ]
    devicehistory_type = 'a_linkDown'

    @staticmethod
    def form_class():
        return LinkStateForm

    def fetch_history(self):
        netbox_history = AlertHistory.objects.select_related(
            'netbox'
        ).filter(
            event_type=LINK_STATE,
            end_time__gte=datetime.max,
            netbox__category__in=self.categories,
            netbox__organization__in=self.organizations,
        ).extra(
            select={
                'downtime': "date_trunc('second', NOW() - start_time)",
                'interfaceid': 'interface.interfaceid',
                'ifname': 'interface.ifname',
            },
            where=['subid = interfaceid::text'],
            tables=['interface']
        ).order_by('-start_time', 'end_time')

        history = []
        for h in netbox_history:
            row = {
                'netboxid': h.netbox.id,
                'alerthistid': h.id,
                'tabrow': (
                    (
                        h.netbox.sysname,
                        reverse('ipdevinfo-details-by-name',
                                args=[h.netbox.sysname])
                    ),
                    (h.netbox.ip, None),
                    (
                        h.ifname,
                        reverse('ipdevinfo-interface-details',
                                args=[h.netbox.sysname, h.interfaceid])
                    ),
                    (h.start_time, None),
                    (h.downtime, None),
                    ('history', reverse('devicehistory-view') +
                '?netbox=%(id)s&eventtype=a_linkDown&group_by=datetime' % {
                    'id': h.netbox.id, }
                    ),
                ),
            }
            history.append(row)
        self.history = history


class SNMPAgentSection(_Section):
    columns = [
        'Sysname',
        'IP',
        'Down since',
        'Downtime',
        '',
    ]
    devicehistory_type = 'a_snmpAgentDown'

    @staticmethod
    def form_class():
        return SNMPAgentForm

    @staticmethod
    def form_data(status_prefs):
        data = {
            'id': status_prefs.id,
            'name': status_prefs.name,
            'type': status_prefs.type,
            'organizations': list(status_prefs.organizations.values_list(
                    'id', flat=True)) or [''],
        }
        data['categories'] = list(status_prefs.categories.values_list(
                'id', flat=True)) or ['']
        return data

    def fetch_history(self):
        netbox_history = AlertHistory.objects.select_related(
            'netbox'
        ).filter(
            event_type=SNMP_STATE,
            end_time__gte=datetime.max,
            netbox__category__in=self.categories,
            netbox__organization__in=self.organizations,
        ).extra(
            select={
                'downtime': "date_trunc('second', NOW() - start_time)",
            }
        ).order_by('-start_time', 'end_time')

        history = []
        for h in netbox_history:
            row = {'netboxid': h.netbox.id,
                   'tabrow': (
                    (
                        h.netbox.sysname,
                        reverse('ipdevinfo-details-by-name',
                            args=[h.netbox.sysname])
                    ),
                    (h.netbox.ip, None),
                    (h.start_time, None),
                    (h.downtime, None),
                    (
                        'history',
                        reverse('devicehistory-view') +
                        ('?netbox=%(id)s&eventtype=a_snmpAgentDown'
                         '&group_by=datetime' % {'id': h.netbox.id})
                    ),
                ),
            }
            history.append(row)
        self.history = history


class PSUSection(_Section):
    columns = [
        'Sysname',
        'IP',
        'PSU',
        'Problem since',
        'Duration',
        '',
    ]
    devicehistory_type = 'a_psuNotOK'

    @staticmethod
    def form_class():
        return ModuleForm

    def fetch_history(self, psu_history=None):
        psu_history = AlertHistory.objects.select_related(
            'netbox', 'device'
        ).filter(
            end_time__gte=datetime.max,
            event_type=PSU_STATE,
            alert_type__name='psuNotOK',
            netbox__organization__in=self.organizations,
            netbox__category__in=self.categories,
        ).extra(
            select={
                'downtime': "date_trunc('second', NOW() - start_time)",
                'powersupply_id': 'powersupply_or_fan.powersupplyid',
                'powersupply_name': 'powersupply_or_fan.name',
            },
            tables=['powersupply_or_fan'],
            where=[
                'alerthist.subid = powersupply_or_fan.powersupplyid::TEXT',
            ],
        ).order_by('-start_time') if psu_history is None else psu_history

        self.history = [self._psu_to_table_row(psu) for psu in psu_history]

    @staticmethod
    def _psu_to_table_row(psu):
        return {'netboxid': psu.netbox.id,
                'tabrow': (
            (psu.netbox.sysname,
             reverse('ipdevinfo-details-by-name', args=[psu.netbox.sysname])),
            (psu.netbox.ip, None),
            (psu.powersupply_name, None),
            (psu.start_time, None),
            (psu.downtime, None),
            ('history',
             (reverse('devicehistory-view') + '?powersupply=%s'
                                              '&eventtype=a_psuNotOK'
                                              '&group_by=datetime' %
                                              psu.powersupply_id)),
        )}
