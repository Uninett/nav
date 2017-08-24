# -*- coding: utf-8 -*-
# Copyright (C) 2016 UNINETT AS
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
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Module for emailing status reports"""

from __future__ import print_function

from datetime import date, datetime, timedelta

from django.core.mail import send_mail
from django.template.loader import render_to_string

from nav.web.business import utils

from collections import namedtuple
Subscription = namedtuple('Subscription', ['to_address', 'period'])
Report = namedtuple('Report', ['subject', 'to_address', 'period',
                               'text_message', 'html_message'])


def send_reports():
    """Sends all reports"""
    subscriptions = [
        Subscription('john.m.bredal@uninett.no', 'month'),
        Subscription('john.m.bredal@uninett.no', 'week'),
    ]

    reports = {}  # Contains reports for the different periods
    for subscription in subscriptions:
        period = subscription.period
        if period not in reports:
            reports[period] = build_report(subscription)
        send_report(reports[period])


def send_report(report):
    """Sends a single email report"""
    send_mail(
        report.subject,
        report.text_message,
        'noreply@example.com',
        [report.to_address],
        html_message=report.html_message
    )


def build_report(subscription):
    """Builds a report for a given subscription period"""
    context = build_context(subscription)
    html_message = render_to_string('business/email.html', context)
    text_message = render_to_string('business/email.txt', context)
    return Report(get_email_subject(subscription), subscription.to_address,
                  subscription.period, text_message, html_message)


def build_context(subscription):
    """Builds a context for the given subscription"""
    midnight = date.today()
    start, end = get_interval(midnight, subscription.period)
    records = utils.get_records(start, end)
    return {
        'start': start,
        'end': end,
        'today': midnight,
        'records': records
    }


def get_interval(sometime, period='month'):
    """Gets the start and end dates for the previous period

    :returns: start and end date objects
    :rtype: datetime.date
    """
    if period == 'month':
        first_day = sometime.replace(day=1)
    elif period == 'week':
        first_day = sometime - timedelta(days=sometime.weekday())

    last_period = first_day - timedelta(days=1)
    start, end = utils.get_interval(last_period, period)
    return convert_to_datetime(start, end)


def convert_to_datetime(*dates):
    """Converts date or datetime objects to date"""
    return [datetime(d.year, d.month, d.day) for d in dates]


def get_email_subject(subscription):
    """Gets the subject for a given subscription"""
    lookup = {
        'month': 'Monthly downtime report for devices in NAV',
        'week': 'Weekly downtime report for devices in NAV',
    }
    return lookup.get(subscription.period)
