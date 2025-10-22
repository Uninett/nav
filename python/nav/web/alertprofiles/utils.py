# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008, 2011 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Utility methods for Alert Profiles"""

import hashlib
import os

from django.db import transaction

import nav.config
import nav.buildconf
from nav.web.auth.utils import get_account
from nav.models.profiles import (
    Filter,
    FilterGroup,
    FilterGroupContent,
    Account,
    AlertSubscription,
    TimePeriod,
)

ADMINGROUP = 1
CONFIGDIR = 'alertprofiles'


def account_owns_filters(account, *filters):
    """
    Verifies that account has access to edit/remove filters and/or filter
    groups.
    """

    # Check if user is admin
    groups = account.groups.filter(pk=ADMINGROUP).count()
    if groups > 0:
        # User is admin
        return True
    else:
        # User is not admin, check each filter
        for filter in filters:
            try:
                if isinstance(filter, (Filter, FilterGroup)):
                    owner = filter.owner
                else:
                    owner = filter.get().owner
            except Account.DoesNotExist:
                # This is a public filter, and we already know that this user
                # is not an admin
                return False
            else:
                if owner == account:
                    return True
                else:
                    return False


def resolve_account_admin_and_owner(request):
    """Primarily used before saving filters and filter groups.
    Gets account, checks if user is admin, and sets owner to a appropriate
    value.
    """
    account = get_account(request)
    admin = account.is_admin()

    owner = None
    if request.POST.get('owner') or not admin:
        owner = account

    return account, admin, owner


@transaction.atomic()
def order_filter_group_content(filter_group):
    """Filter group content is ordered by priority where each filters priority
    is the previous filters priority incremented by one, starting at 1. Here we
    loop through all the filters and check if they are ordered that way, and if
    they are not, we order them that way.

    Returns the last filters priority (0 if there are no filters)
    """
    filter_group_content = FilterGroupContent.objects.filter(
        filter_group=filter_group.id
    ).order_by('priority')

    if filter_group_content:
        prev_priority = 0
        for f in filter_group_content:
            priority = f.priority
            if priority - prev_priority != 1:
                f.priority = prev_priority + 1
                f.save()
            prev_priority = f.priority

        return prev_priority
    else:
        return 0


def read_time_period_templates():
    templates = {}
    template_dir = nav.config.find_config_file(CONFIGDIR)
    template_configs = os.listdir(template_dir)

    for template_file in template_configs:
        if '.conf' in template_file:
            filename = os.path.join(template_dir, template_file)
            key = hashlib.md5(filename.encode('utf-8')).hexdigest()
            config = nav.config.getconfig(filename)
            templates[key] = config

    return templates


def alert_subscriptions_table(periods):
    weekday_subscriptions = []
    weekend_subscriptions = []
    shared_class_id = 0

    alert_subscriptions = AlertSubscription.objects.select_related(
        'time_period', 'filter_group', 'alert_address'
    ).filter(time_period__in=periods)

    for p in periods:
        valid_during = p.valid_during

        subscriptions = []
        for s in alert_subscriptions:
            if s.time_period == p:
                subscriptions.append(s)

        # This little snippet magically assigns a class to shared time periods
        # so they appear with the same highlight color.
        if valid_during == TimePeriod.ALL_WEEK:
            p.css_class = 'shared' + str(shared_class_id)
            shared_class_id += 1
            if shared_class_id > 7:
                shared_class_id = 0

        # For usability we change 'all days' periods to one weekdays and one
        # weekends period.
        # Because we might add the same period to both weekdays and weekends we
        # must make sure at least one of them is a copy, so changes to one of
        # them don't apply to both.
        if valid_during in (TimePeriod.WEEKDAYS, TimePeriod.ALL_WEEK):
            weekday_subscriptions.append(
                {
                    'time_period': p,
                    'alert_subscriptions': subscriptions,
                }
            )
        if valid_during in (TimePeriod.WEEKENDS, TimePeriod.ALL_WEEK):
            weekend_subscriptions.append(
                {
                    'time_period': p,
                    'alert_subscriptions': subscriptions,
                }
            )

    subscriptions = [
        {'title': 'Weekdays', 'subscriptions': weekday_subscriptions},
        {'title': 'Weekends', 'subscriptions': weekend_subscriptions},
    ]

    # There's not stored any information about a end time in the DB, only start
    # times, so the end time of one period is the start time of the next
    # period.
    for type in subscriptions:
        subscription = type['subscriptions']
        for i, s in enumerate(subscription):
            if i < len(subscription) - 1:
                end_time = subscription[i + 1]['time_period'].start
            else:
                end_time = subscription[0]['time_period'].start
            s['time_period'].end = end_time

    return subscriptions
