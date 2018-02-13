"""A stupid util module for business reports"""

import calendar
from datetime import datetime, timedelta
from collections import defaultdict, namedtuple

from nav.models.event import AlertHistory
from nav.models.manage import Interface
from nav.models.profiles import ReportSubscription
from django.db.models import Q

AvailabilityRecord = namedtuple(
    'AvailabilityRecord', ['subject', 'incidents', 'downtime', 'availability'])


class LinkSubject(object):
    """Adapter for link subjects"""
    def __init__(self, subject):
        self.subject = subject

    def get_absolute_url(self):
        return self.subject.get_absolute_url()

    def __str__(self):
        return "{o.ifname} ({o.ifalias}) on {o.netbox}".format(o=self.subject)


def get_interval(sometime, interval):
    """Gets the interval for some time

    :param sometime: A datetime.datetime object
    :param interval: A string to indicate interval
    :returns: The start and endtime for the interval
    :rtype: datetime.datetime, datetime.datetime
    """
    year = sometime.year
    month = sometime.month
    if interval == ReportSubscription.MONTH:
        _day, days = calendar.monthrange(year, month)
        start = datetime(year, month, 1)
        end = datetime(year, month, days) + timedelta(days=1)
    elif interval == ReportSubscription.WEEK:
        start = sometime - timedelta(days=sometime.weekday())
        end = start + timedelta(days=7)
    else:
        # interval is one day
        start = sometime
        end = start + timedelta(days=1)
    return start, end


def get_months(number_of_months=12):
    """Returns a list of datetime objects for each month

    The date is set to the first date in the month.
    The first date is the previous months first day

    :rtype: list[datetime.datetime]
    """
    now = datetime.now()
    month = datetime(now.year, now.month, 1)
    months = [month]
    for _ in range(number_of_months):
        month = (month - timedelta(days=1)).replace(day=1)
        months.append(month)

    return months


def compute_downtime(alerts, start, end):
    """Computes the total downtime for the given alerts"""
    downtime = timedelta()
    for alert in alerts:
        start_inside_interval = start <= alert.start_time <= end
        end_inside_interval = start <= alert.end_time <= end

        if start_inside_interval or end_inside_interval:
            # I want one liners dammit! :p
            # pylint: disable=C0301
            interval_start = alert.start_time if start_inside_interval else start
            interval_end = alert.end_time if end_inside_interval else end
            downtime += (interval_end - interval_start)
        elif alert.start_time <= start and alert.end_time >= end:
            # If the alert covers the whole interval
            downtime += (end - start)

    return downtime


def compute_availability(downtime, interval):
    """Computes the availability given downtime and interval"""
    availability = 1.0
    fraction = downtime.total_seconds() / interval.total_seconds()
    availability = availability - fraction

    return availability * 100


def create_record(subject, alerts, start, end):
    """Creates an availability record based on a subject' alerts in a period"""
    downtime = compute_downtime(alerts, start, end)
    interval = end - start
    availability = compute_availability(downtime, interval)

    # Cheekily remove microseconds
    downtime = downtime - timedelta(microseconds=downtime.microseconds)

    return AvailabilityRecord(get_subject(subject), alerts, downtime,
                              availability)


def get_subject(subject):
    """Get the string representation of this subject"""
    if isinstance(subject, Interface):
        return LinkSubject(subject)

    return subject


def get_alerts(start, end, eventtype='boxState', alerttype='boxDown'):
    """Gets the alerts for the given start-end interval"""
    return AlertHistory.objects.filter(
        event_type=eventtype, end_time__isnull=False,
        alert_type__name=alerttype).filter(
            Q(end_time__range=(start, end)) |
            Q(start_time__range=(start, end)) |
            (Q(start_time__lte=start) & Q(end_time__gte=end)
            )).order_by('-start_time')


def group_by_netbox(alerts):
    """Group alerts by netbox"""
    grouped_alerts = defaultdict(list)
    for alert in alerts:
        grouped_alerts[alert.netbox].append(alert)
    return grouped_alerts


def group_by_interface(alerts):
    grouped_alerts = defaultdict(list)
    for alert in alerts:
        try:
            interface = Interface.objects.get(pk=alert.subid)
        except Interface.DoesNotExist:
            continue
        else:
            grouped_alerts[interface].append(alert)
    return grouped_alerts


def get_netbox_records(start, end):
    alerts = get_alerts(start, end, 'boxState', 'boxDown')
    grouped_alerts = group_by_netbox(alerts)
    return [create_record(subject, alerts, start, end)
            for subject, alerts in grouped_alerts.items()]


def get_interface_records(start, end):
    alerts = get_alerts(start, end, 'linkState', 'linkDown')
    grouped_alerts = group_by_interface(alerts)
    return [create_record(subject, alerts, start, end)
            for subject, alerts in grouped_alerts.items()]
