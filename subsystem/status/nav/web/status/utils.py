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

from django.db import transaction

from nav.models.profiles import Account, StatusPreference

def extract_post(post):
    '''Some browser don't support buttons with names and values, so we have to
    use input type="submit" instead.

    The result is that:
        instead of
            <button name="foo" value="bar">Do foobar</button>
        we use
            <input type="submit" name="foo=bar" value="Do foobar />

    This function extracts the values. So if the name was foo=bar, we now got
    the name foo with value bar.
    '''
    for name in post:
        if name.find('=') != -1:
            key, value = name.split('=')
            del post[name]
            post[key] = value
    return post

@transaction.commit_on_success
def order_status_preferences(account):
    prefs = StatusPreference.objects.filter(
        account=account
    ).order_by('position')

    if len(prefs) > 0:
        prev_position = 0
        for pref in prefs:
            if pref.position - prev_position != 1:
                pref.position = prev_position + 1
                pref.save()
            prev_position = pref.position
        return prev_position
    else:
        return 0

@transaction.commit_on_success
def make_default_preferences(account):
    sections = StatusPreference.objects.filter(
        account=Account.DEFAULT_ACCOUNT
    )
    for section in sections:
        StatusPreference.objects.create(
            name=section.name,
            position=section.position,
            type=section.type,
            account=account,
            services=section.services,
            states=section.states,
        )

#def convert_old_preferences(account):
#    ALL_SELECTED = 'all_selected_tkn'
#
#    preferences = AccountProperty.objects.filter(
#        account=account,
#        property='statusprefs',
#    )
#    for p in preferences:
#        data = cPickle.loads(p.value.encode('utf-8'))
#        (iDunno, type, name, prefs) = data
#        organizations = prefs.get('orgid', [])
#        categories = prefs.get('catid', [])
#        services = prefs.get('handler', None)
#        states = prefs.get('states', None)
#
#        section = StatusPreference(
#            name=name,
#            type=type,
#            account=account,
#        )
#
#        if services and services[0] != ALL_SELECTED:
#            section.services = ",".join(services)
#        if states and states[0] != ALL_SELECTED:
#            section.states = ",".join(states)
#
#        section.save()
