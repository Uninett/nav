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
    '''Handles all new and user queued alerts'''

    # Alot of this functionality could have been backed into the models for the
    # corresponding objects, however it seems better to keep all of this logic
    # in one place. Despite this some the simpler logic has been offloaded to
    # the models themselves.

    new_alerts = AlertQueue.objects.all()[:10]
    accounts = []

    # Build datastructure that contains accounts and corresponding
    # filtergroupcontent_sets so that we don't redo db queries to much
    for account in Account.objects.filter(alertpreference__active_profile__isnull=False):
            current_alertsubscriptions = account.get_active_profile().get_active_timeperiod().alertsubscription_set.all()

            tmp = []
            for alertsubscription in current_alertsubscriptions:
                tmp.append( (alertsubscription, alertsubscription.filter_group.filtergroupcontent_set.all()) )

            if tmp:
                permisions = FilterGroupContent.objects.filter(filter_group__group_permisions__accounts=account)
                accounts.append( (account, tmp, permisions) )

    # Check all acounts against all their active subsriptions
    for account, alertsubscriptions, permisions in accounts:
        logging.debug("Cheking alerts for account '%s'" % account)

        for alert in new_alerts:
            for alertsubscription, filtergroupcontents in alertsubscriptions:

                # Check if alert matches, and if user has permision
                if check_alert_against_filtergroupcontents(alert, filtergroupcontents):
                    if check_alert_against_filtergroupcontents(alert, permisions):
                        alertsubscription.handle_alert(alert)
                    else:
                        logging.debug('alert %d not: sent to %s due to lacking permisions' % (alert.id, account))
                else:
                    logging.debug('alert %d: did not match the alertsubscription %d of user %s' % (alert.id, alertsubscription.id, account))

    # FIXME handle AccountAlertQueue
#    for alert in AccountAlertQueue.objects.all():

    # FIXME update the state for which alerts have been handeled

def check_alert_against_filtergroupcontents(alert, filtergroupcontents):
    '''Checks a given alert against an array of filtergroupcontents'''

    # Allways assume that the match will fail
    matches = False

    for content in filtergroupcontents:
        original_macthes = matches

        # If we have not matched the message see if we can match it
        if not matches and content.include:
            matches = content.filter.check(alert) == content.positive

            if matches: logging.debug('alert %d: got included by filter %d' % (alert.id, content.filter.id))

        # If the alert has been matched try excluding it
        elif matches and not content.include:
            matches = content.filter.check(alert) == content.positive

            # Log that we excluded the alert
            if not matches:
                logging.debug('alert %d got: excluded by filter %d' % (alert.id, content.filter.id))

        if original_macthes == matches:
            logging.debug('alert %d: unaffected by filter %d' % (alert.id, content.filter.id))
    return matches
