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

from nav.web.status.filters import OrganizationFilter, CategoryFilter, \
    StateFilter, ServiceFilter

def get_user_sections(account):
    sections = []
    preferences = StatusPreference.objects.filter(
        account=account
    ).order_by('position')

    for pref in preferences:
        if pref.type == StatusPreference.SECTION_NETBOX:
            section.append(NetboxSection(account,
                name=pref.name,
                organisations=pref.organisations.values_list('id', flat=True),
                categories=pref.categories.values_list('id', flat=True),
                states=pref.state_set.values_list('state', flat=True)
            ))
        elif pref.type == StatusPreference.SECTION_MODULE:
            pass
        elif pref.type == Status.SECTION_SERVICE:
            pass

    return sections

class _Section(object):
    '''Base class for sections. Defines an interface of methods available in
    all sections.
    '''
    def __init__(self, **kwargs):
        self.name = kwargs.pop('name')

    def get_name(self):
        '''Returns a string with the name of the section'''
        return ''

    def get_columns(self):
        '''Returns a list of all columns of this section'''
        return []

    def get_next_row(self):
        '''Returns the next row'''
        yield None

    def get_filters(self):
        '''Returns a list of all filters available'''
        ret = {}
        for key, value in self.__dict__.items():
            if issubclass(value, Filter):
                ret[key] = value
        return ret

class NetboxSection(_Section):
    categories = CategoryFilter()
    states = StateFilter()

    def __init__(self,account, **kwargs):
        self.organisations = OrganizationFilter(account)
        organisations.set_selected(kwargs.pop('organisations'))
        categories.set_selected(kwargs.pop('categories'))
        states.set_selected(kwrags.pop('states'))

        super(_Section, self).__init__(**kwargs)

    def _maintenance(self):
        try:
            return self._maintenance_query
        except AttributeError:
            self._maintenance_query = AlertHistory.objects.filter(
                event_type='mainenanceState',
                end_time__gt=datetime.max,
            ).values('pk').query
            return self._maintenance_query

    def all(self):
        history = AlertHistory.objects.filter(
            ~Q(id__in=self._maintenance()),
            event_type__id='boxState',
            end_time__gt=datetime.max,
            netbox__up__in=self.states.filter(),
            netbox__category__in=self.category.filter(),
            netbox__organisation__in=self.organisation.filter(),
        ).order_by('-start_time', 'end_time')
