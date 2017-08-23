#!/usr/bin/env python

import csv
from datetime import date, datetime, timedelta

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Q

from nav.web.business import utils
from nav.models.event import AlertHistory


class AlertAdapter(dict):

    fields = ['Subject', 'Start', 'End']

    def __init__(self, alert):
        self.alert = alert
        dict.__init__(self, {
            'Subject': alert.netbox,
            'Start': alert.start_time,
            'End': alert.end_time
        })


def main():
    html_template = 'business/email.html'
    text_template = 'business/email.txt'

    # period = 'week'
    period = 'month'
    # now = datetime.now()
    # midnight = datetime(year=now.year, month=now.month, day=now.day)
    midnight = date.today()
    start, end = get_interval(midnight, period)

    print start

    alerts = get_alerts(start, end)
    active_alerts = alerts.filter(end_time__gte=datetime.max)
    inactive_alerts = alerts.exclude(end_time__gte=datetime.max)
    context = {
        'start': start,
        'end': end,
        'today': midnight,
        'active_alerts': active_alerts,
        'inactive_alerts': inactive_alerts
    }

    html_message = render_to_string(html_template, context)
    text_message = render_to_string(text_template, context)

    print text_message

    # send_mail(
    #     'Email subject',
    #     text_message,
    #     'noreply@example.com',
    #     ['john.m.bredal@uninett.no'],
    #     html_message=html_message
    # )


def get_interval(sometime, period='month'):
    if period == 'month':
        first_day = sometime.replace(day=1)
    elif period == 'week':
        first_day = sometime - timedelta(days=sometime.weekday())

    last_period = first_day - timedelta(days=1)
    return utils.get_interval(last_period, period)


def get_alerts(start, end):
    eventtype='boxState'
    alerttype='boxDown'

    return AlertHistory.objects.filter(
        event_type=eventtype, end_time__isnull=False,
        alert_type__name=alerttype).filter(
            Q(end_time__range=(start, end)) |
            Q(start_time__range=(start, end)) |
            (Q(start_time__lte=start) & Q(end_time__gte=end)
            )).order_by('-start_time')


if __name__ == '__main__':
    main()
