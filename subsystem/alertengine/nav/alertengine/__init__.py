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

from django.db import transaction

from nav.models.profiles import Account, AccountAlertQueue, FilterGroupContent, AlertSubscription, AlertAddress
from nav.models.event import AlertQueue

logger = logging.getLogger('nav.alertengine')

@transaction.commit_on_success
def check_alerts(debug=False):
    '''Handles all new and user queued alerts'''

    # We use transaction autocommit so that the changes we make only propogate
    # if the entire loop finishes.

    # Alot of this functionality could have been backed into the models for the
    # corresponding objects, however it seems better to keep all of this logic
    # in one place. Despite this some the simpler logic has been offloaded to
    # the models themselves.

    # Try to avoid spamming people when running tests
    if debug:
        AlertAddress.DEBUG_MODE = True

    now = datetime.now()
    accounts = []
    sent_new = 0
    sent_queued = 0

    # Get all alerts that aren't in alert queue due to subscription
    new_alerts = AlertQueue.objects.filter(accountalertqueue__isnull=True)

    # Get all queued alerts that have been inserted in the past.
    queued_alerts = AccountAlertQueue.objects.filter(insertion_time__lt=now)

    if not len(new_alerts) and not len(queued_alerts):
        logger.debug('No new alerts or account queued alerts to process')
        return

    logger.info('Starting alertengine run, checking %d new alerts and %d alerts in user queue' % (len(new_alerts), len(queued_alerts)))

    if len(new_alerts):
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

        # Check all acounts against all their active subscriptions
        for account, alertsubscriptions, permisions in accounts:
            logger.debug("Cheking alerts for account '%s'" % account)

            for alert in new_alerts:
                for alertsubscription, filtergroupcontents in alertsubscriptions:
                    # Check if alert matches, and if user has permision
                    if check_alert_against_filtergroupcontents(alert, filtergroupcontents):
                        if check_alert_against_filtergroupcontents(alert, permisions, type='permision check'):
                            alertsubscription.handle_alert(alert)
                            # FIXME this is wrong
                            sent_new += 1
                        else:
                            logger.warn('alert %d not: sent to %s due to lacking permisions' % (alert.id, account))
                    else:
                        logger.info('alert %d: did not match the alertsubscription %d of user %s' % (alert.id, alertsubscription.id, account))

    # We want to keep track of wether or not any weekly or daily messages have
    # been sent so that we can update the state of the users
    # last_sent_daily/weekly
    sent_weekly = False
    sent_daily = False

    if len(queued_alerts):
        for queued_alert in queued_alerts:
            try:
                subscription = queued_alert.subscription
            except AlertSubscription.DoesNotExist:
                logger.warn('account queued alert %d does not have subscription, probably a legacy table row' % queued_alert.id)
                continue

            logger.info('stored alert %d: Checking if we should send alert to %s due to %s subscription' % (queued_alert.alert.id, queued_alert.account, subscription.get_type_display()) )

            if subscription.type == AlertSubscription.NOW:
                # Send right away if the subscription has been changed to now
                queued_alert.send()
                sent_queued += 1

            elif subscription.type == AlertSubscription.DAILY:
                daily_time = subscription.time_period.profile.daily_dispatch_time
                last_sent  = subscription.time_period.profile.alertpreference.last_sent_day or datetime.min

                # If the last sent date is less than the current date, and we are
                # past the daily time and the alert was added to the queue before
                # this time

                logger.debug('Tests: last sent %s, daily time %s, insertion time %s' % (last_sent.date() < now.date(), daily_time < now.time(), queued_alert.insertion_time.time() < daily_time))

                if last_sent.date() < now.date() and daily_time < now.time() and queued_alert.insertion_time.time() < daily_time:
                    queued_alert.send()
                    sent_queued += 1
                    sent_daily = True

            elif subscription.type == AlertSubscription.WEEKLY:
                weekly_time = subscription.time_period.profile.weekly_dispatch_time
                weekly_day = subscription.time_period.profile.weekly_dispatch_day
                last_sent  = subscription.time_period.profile.alertpreference.last_sent_week or datetime.min

                # Check that we are at the correct weekday, and that the last sent
                # time is less than today, and that alert was inserted before the
                # weekly time.
                logger.debug('Tests: weekday %s, last sent %s, weekly time %s, insertion time %s' % (weekly_day == now.weekday(), last_sent.date() < now.date(), weekly_time < now.time(), queued_alert.insertion_time.time() < weekly_time))

                if weekly_day == now.weekday() and last_sent.date() < now.date() and weekly_time < now.time() and queued_alert.insertion_time.time() < weekly_time:
                    queued_alert.send()
                    sent_queued += 1
                    sent_weekly = True

            elif subscription.type == AlertSubscription.NEXT:
                current_time_period = subscription.alert_address.account.get_active_profile().get_active_timeperiod()
                insertion_time = queued_alert.insertion_time
                queued_alert_time_period = subscription.time_period

                # Send if we are in a different time period than the one that the
                # message was inserted with.
                logger.debug('Tests: different time period %s' % (queued_alert_time_period.id != current_time_period.id))

                # Check if the message was inserted on a previous day and that the
                # start period of the time period it was inserted in has passed.
                # This check should catch the corner case where a user only has one
                # timeperiod that loops.
                logger.debug('Tests: different day %s, insertion time %s' % (insertion_time.date() < now.date(), insertion_time.time() < queued_alert_time_period.start))

                if subscription.time_period.id != current_time_period.id:
                    queued_alert.send()
                    sent_queued += 1
                elif insertion_time.date() < now.date() and insertion_time.time() < queued_alert_time_period.start:
                    queued_alert.send()
                    sent_queued += 1

            else:
                logger.error('account %s has an invalid subscription type in subscription %d' % (subscription.account, subscription.id))

    # Update the when the user last recieved daily or weekly alerts.
    if sent_daily:
        account.alertpreference.last_sent_day = now
    if sent_weekly:
        account.alertpreference.last_sent_weekly = now

    alerts_in_account_queues = [a.alert_id for a in AccountAlertQueue.objects.all()]

    # Delete handeled alerts that are not in an AccountAlertQueue
    if new_alerts:
        # Get id's of alerts that have been queued for users.

        if not debug:
            to_delete = AlertQueue.objects.filter(id__in=[a.id for a in new_alerts]).exclude(id__in=alerts_in_account_queues)
            logger.info('Deleted following alerts from alert queue: %s' % ([a.id for a in to_delete]))
            to_delete.delete()
        else:
            logger.info('In testing mode: would have deleted following alerts from alert queue: %s' % ([a.id for a in new_alerts]))

    if alerts_in_account_queues:
        logger.info('Alerts %s keept in alert queue as they are still needed by user subscriptions' % (alerts_in_account_queues))

    logger.info('Finished alertengine run, sent %d new alerts and %d user queued alerts, %d user queued alerts left in queue' % (sent_new, sent_queued, len(alerts_in_account_queues)))


def check_alert_against_filtergroupcontents(alert, filtergroupcontents, type='match check'):
    '''Checks a given alert against an array of filtergroupcontents'''

    # Allways assume that the match will fail
    matches = False

    for content in filtergroupcontents:
        original_macthes = matches

        # If we have not matched the message see if we can match it
        if not matches and content.include:
            matches = content.filter.check(alert) == content.positive

            if matches: logger.debug('alert %d: got included by filter %d in %s' % (alert.id, content.filter.id, type))

        # If the alert has been matched try excluding it
        elif matches and not content.include:
            matches = content.filter.check(alert) == content.positive

            # Log that we excluded the alert
            if not matches:
                logger.debug('alert %d got: excluded by filter %d in %s' % (alert.id, content.filter.id, type))

        if original_macthes == matches:
            logger.debug('alert %d: unaffected by filter %d in %s' % (alert.id, content.filter.id, type))
    return matches
