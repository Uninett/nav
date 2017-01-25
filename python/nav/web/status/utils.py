#
# Copyright (C) 2009-2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details. You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django.db import transaction

from nav.models.profiles import Account, StatusPreference

from nav.web.status.forms import SectionForm, NetboxForm
from nav.web.status.forms import NetboxMaintenanceForm, ServiceForm
from nav.web.status.forms import ServiceMaintenanceForm, ModuleForm
from nav.web.status.forms import ThresholdForm


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


@transaction.atomic()
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


@transaction.atomic()
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
