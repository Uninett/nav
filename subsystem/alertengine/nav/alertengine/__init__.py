#! /usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2006 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
Package placeholder. If you remove it, the package won't work.
"""

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Thomas Adamcik (thomas.adamcik@uninett.no)"
__id__ = "$Id$"

import logging
from pprint import pprint

from django.db.models import Q

from nav.models.profiles import Account, AccountAlertQueue, FilterGroupContent
from nav.models.event import AlertQueue

logging.basicConfig(level=logging.DEBUG)

def check_alerts():
    new_alerts = AlertQueue.objects.new_alerts()
    accounts = []

    # Build datastructure that contains accounts and corresponding
    # filtergroupcontent_sets so that we don't risk redoing queuries all the
    # time
    for account in Account.objects.filter(alertpreference__active_profile__isnull=False):
            logging.debug("Cheking alerts for account '%s'" % account)

            current_alertsubscriptions = account.get_active_profile().get_active_timeperiod().alertsubscription_set.all()

            tmp = []
            for alertsubscription in current_alertsubscriptions:
                tmp.append( (alertsubscription, alertsubscription.filter_group.filtergroupcontent_set.all()) )

            if tmp:
                permisions = FilterGroupContent.objects.filter(filter_group__group_permisions__accounts=account)

                accounts.append( (account, tmp, permisions) )

    for account, alertsubscriptions, permisions in accounts:
        for alertsubscription, filtergroupcontents in alertsubscriptions:
            matches = check_alert_against_filtergroupcontents(None, filtergroupcontents)

            if matches:
                if check_alert_against_filtergroupcontents(alert, permisions):
                    logging.debug('Sending message')
                else:
                    logging.debug('alert matched but permision test rejected alert')
            else:
                logging.debug('did not match')

def check_alert_against_filtergroupcontents(alert, filtergroupcontents):
    matches = False

    for content in filtergroupcontents:
        if not matches and content.include:
            # If we have not matched the message see if we can match it
            matches = content.filter.check(alert) == content.positive

        elif matches and not content.include:
            # See if we can exlcude the message
            matches = content.filter.check(alert) == content.positive

            if not matches:
                # If matches has become false we excluded the message
                # for good.
                continue
    return matches
