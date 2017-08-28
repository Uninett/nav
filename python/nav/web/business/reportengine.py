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

from collections import namedtuple
from datetime import date, datetime, timedelta

from django.core.mail import send_mail
from django.template.loader import render_to_string

from nav.web.business import utils
from nav.models.profiles import ReportSubscription


Report = namedtuple('Report', ['subject', 'period', 'text_message',
                               'html_message'])


def send_reports(period):
    """Sends all reports for the given period

    Supported periods are in the ReportSubscription class
    """
    report = build_report(period)
    for subscription in ReportSubscription.objects.filter(period=period):
        send_report(report, subscription.address.address)


def send_report(report, to_address):
    """Sends a single email report"""
    send_mail(
        report.subject,
        report.text_message,
        'noreply@example.com',
        [to_address],
        html_message=report.html_message
    )


def build_report(period):
    """Builds a report for a given subscription period"""
    context = build_context(period)
    html_message = render_to_string('business/email.html', context)
    text_message = render_to_string('business/email.txt', context)
    return Report(get_email_subject(period), period, text_message, html_message)


def build_context(period):
    """Builds a context for the given subscription"""
    midnight = date.today()
    start, end = get_last_interval(midnight, period)
    records = utils.get_records(start, end)
    return {
        'start': start,
        'end': end,
        'today': midnight,
        'records': records
    }


def get_last_interval(sometime, period):
    """Gets the start and end dates for the previous period

    This means that if `sometime` is a datetime object from the current month
    and `period` indicates month, then this function will return two
    datetime-objects - the first one is the first day of _previous_ month and
    the second one is the first day of the _current_ month.

    :returns: start and end date objects
    :rtype: datetime.date
    """
    if period == ReportSubscription.MONTH:
        first_day = sometime.replace(day=1)
    elif period == ReportSubscription.WEEK:
        first_day = sometime - timedelta(days=sometime.weekday())
    else:
        first_day = sometime  # Daily

    last_period = first_day - timedelta(days=1)
    start, end = utils.get_interval(last_period, period)
    return convert_to_datetime(start, end)


def convert_to_datetime(*dates):
    """Converts date or datetime objects to date"""
    return [datetime(d.year, d.month, d.day) for d in dates]


def get_email_subject(period):
    """Gets the subject for a given subscription"""
    lookup = {
        ReportSubscription.MONTH: 'Monthly downtime report for devices in NAV',
        ReportSubscription.WEEK: 'Weekly downtime report for devices in NAV',
        ReportSubscription.DAY: 'Daily downtime report for devices in NAV',
    }
    return lookup.get(period)
