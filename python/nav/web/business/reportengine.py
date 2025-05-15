# -*- coding: utf-8 -*-
# Copyright (C) 2016 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Module for emailing status reports"""

import logging
from collections import namedtuple
from datetime import date, datetime, timedelta
from operator import attrgetter

from django.core.mail import send_mail
from django.template.loader import render_to_string

from nav.web.business import utils
from nav.models.profiles import ReportSubscription
from nav.django.settings import DEFAULT_FROM_EMAIL

_logger = logging.getLogger(__name__)
Report = namedtuple('Report', ['subject', 'period', 'text_message', 'html_message'])


def send_reports(period):
    """Sends all reports for the given period

    Supported periods are in the ReportSubscription class
    """

    report_types = [t for t, _ in ReportSubscription.TYPES]
    for report_type in report_types:
        _logger.debug('Sending reports for period %s, type %s', period, report_type)
        subscriptions = ReportSubscription.objects.filter(
            period=period, report_type=report_type
        )
        for subscription in subscriptions:
            report = build_report(period, report_type, subscription.exclude_maintenance)
            send_report(report, subscription.address.address)
        _logger.info(
            '%s %s availability: Sent %s reports',
            period,
            report_type,
            subscriptions.count(),
        )


def send_report(report, to_address):
    """Sends a single email report"""
    _logger.debug('Sending report to %s', to_address)
    send_mail(
        report.subject,
        report.text_message,
        DEFAULT_FROM_EMAIL,
        [to_address],
        html_message=report.html_message,
    )


def build_report(period, report_type, exclude_maintenance=False):
    """Builds a report for a given subscription period"""
    context = build_context(period, report_type, exclude_maintenance)
    html_message = render_to_string('business/email.html', context)
    text_message = render_to_string('business/email.txt', context)
    return Report(
        get_email_subject(period, report_type), period, text_message, html_message
    )


def build_context(period, report_type, exclude_maintenance=False):
    """Builds a context for the given subscription"""
    midnight = datetime.combine(date.today(), datetime.min.time())
    start, end = get_last_interval(midnight, period)
    lookup = {
        ReportSubscription.DEVICE: utils.get_netbox_records,
        ReportSubscription.LINK: utils.get_interface_records,
    }
    records = lookup[report_type](start, end, exclude_maintenance)
    sorted_records = sorted(records, key=attrgetter('downtime'), reverse=True)
    max_length = 30
    if records:
        max_length = max(len(str(r.subject)) for r in records)

    return {
        'start': start,
        'end': end,
        'today': midnight,
        'records': sorted_records,
        'exclude_maintenance': exclude_maintenance,
        'subject_format': "-{}s".format(max_length),
    }


def get_last_interval(sometime, period):
    """Gets the start and end dates for the previous period

    This means that if `sometime` is a datetime object from the current month
    and `period` indicates month, then this function will return two
    datetime-objects - the first one is the first day of _previous_ month and
    the second one is the first day of the _current_ month.

    :returns: start and end date objects
    :rtype: list[datetime.datetime]
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


def get_email_subject(period, report_type):
    """Creates an email subject for the report"""
    title = "{} {}".format(
        ReportSubscription.get_period_description(period),
        ReportSubscription.get_type_description(report_type),
    ).title()
    return "{} report from NAV".format(title)
