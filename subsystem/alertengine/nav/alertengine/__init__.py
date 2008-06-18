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
from datetime import datetime

from django.db.models import Q

from nav.models.profiles import Account, AccountAlertQueue, FilterGroupContent, AlertSubscription
from nav.models.event import AlertQueue

logging.basicConfig(level=logging.DEBUG)

def check_alerts():
    '''Handles all new and user queued alerts'''

    # Alot of this functionality could have been backed into the models for the
    # corresponding objects, however it seems better to keep all of this logic
    # in one place. Despite this some the simpler logic has been offloaded to
    # the models themselves.

    new_alerts = AlertQueue.objects.all()[:5]
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


    now = datetime.now()

    # We want to keep track of wether or not any weekly or daily messages have
    # been sent.
    sent_weekly = False
    sent_daily = False

    for queued_alert in AccountAlertQueue.objects.all():
        try:
            subscription = queued_alert.subscription
        except AlertSubscription.DoesNotExist:
            logging.warn('account queued alert %d does not have subscription, probably a legacy table row' % queued_alert.id)
            continue

        if subscription.type == AlertSubscription.NOW:
            # Send right away if the subscription has been changed to now
            queued_alert.send()

        elif subscription.type == AlertSubscription.DAILY:
            daily_time = subsription.time_period.profile.time
            last_sent  = subsription.time_period.profiles.alertpreference.last_sent_day

            # If the last sent date is less than the current date, and we are
            # past the daily time and the alert was added to the queue before
            # this time
            if last_sent.date() < now.date() and daily_time < now.time() and queued_alert.insertion_time < daily_time:
                queued_alert.send()
                sent_daily = True

        elif subscription.type == AlertSubscription.WEEKLY:
            weekly_time = subscription.time_period.profile.weektime
            weekly_day = subscription.time_period.profile.weekday
            last_sent  = subscription.time_period.profile.alertpreference.last_sent_week

            # Check that we are at the correct weekday, and that the last sent
            # time is less than today, and that alert was inserted before the
            # weekly time.
            if weekly_day == now.weekday() and last_sent.date() < now.date() and weekly_time < now.time() and queued_alert.insertion_time.time() < weekly_time:
                queued_alert.send()
                sent_weekly = True

        elif subsription.type == AlertSubscription.NEXT:
            current_time_period = account.get_active_profile().get_active_timeperiod()
            insertion_time = queued_alert.insertion_time
            queued_alert_time_period = subscription.time_period

            # Send if we are in a different time period than the one that the
            # message was inserted with.
            if subscription.time_period.id != current_time_period.id:
                queued_alert.send()
            # Check if the message was inserted on a previous day and that the
            # start period of the time period it was inserted in has passed.
            # This check should catch the corner case where a user only has one
            # timeperiod that loops.
            elif insertion_time.date() < now.date() and insertion_time.time() < queued_alert_time_period.time:
                queued_alert.send()

        else:
            logging.warn('account %s has an invalid subscription type in subsription %d' % (subsription.account, subsription.id))

    # Update the when the user last recieved daily or weekly alerts.
    if sent_daily:
        account.alertpreference.last_sent_day = now
    if sent_weekly:
        account.alertpreference.last_sent_weekly = now

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
