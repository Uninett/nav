"""A stupid util module for business reports"""

import calendar
from datetime import datetime, timedelta
from collections import defaultdict, namedtuple
import logging

from nav.models.event import AlertHistory
from nav.models.manage import Interface, Netbox
from nav.models.profiles import ReportSubscription

_logger = logging.getLogger(__name__)

AvailabilityRecord = namedtuple(
    'AvailabilityRecord',
    ['subject', 'incidents', 'downtime', 'availability', 'maintenances'],
)


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
    return start, min(end, datetime.now())


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


def compute_availability(downtime, interval):
    """Computes the availability given downtime and interval"""
    if downtime.total_seconds() == 0 or not interval:
        return 100
    availability = 1.0
    fraction = downtime.total_seconds() / interval.total_seconds()
    availability = max(availability - fraction, 0.0)
    return availability * 100


def create_record(subject, alerts, start, end, maintenances=None):
    """Creates an availability record based on a subject's alerts in a period"""

    def duration(alert):
        return alert.end_within - alert.start_within

    downtime = sum((duration(a) for a in alerts), timedelta())
    if maintenances:
        maintenancetime = sum((duration(m) for m in maintenances), timedelta())
        downtime -= maintenancetime

    availability = compute_availability(downtime, end - start)

    # Cheekily remove microseconds
    downtime = downtime - timedelta(microseconds=downtime.microseconds)

    return AvailabilityRecord(
        get_subject(subject), alerts, downtime, availability, maintenances
    )


def get_subject(subject):
    """Get the string representation of this subject"""
    if isinstance(subject, Interface):
        return LinkSubject(subject)

    return subject


def group_by_subject(alerts, subject_filter=None):
    grouped_alerts = defaultdict(list)
    for alert in alerts:
        subject = alert.get_subject()
        if subject_filter and not isinstance(subject, subject_filter):
            continue
        grouped_alerts[subject].append(alert)
    return grouped_alerts


def get_netbox_records(start, end, exclude_maintenance=False):
    alerts = get_alert_periods_by_type(start, end, 'boxState', ['boxDown'])
    grouped_alerts = group_by_subject(alerts, Netbox)

    if exclude_maintenance:
        maintenances = get_alert_periods_by_type(
            start, end, 'maintenanceState', ['onMaintenance']
        )
        grouped_maintenance = group_by_subject(maintenances)
    else:
        grouped_maintenance = {}

    records = (
        create_record(netbox, alerts, start, end, grouped_maintenance.get(netbox))
        for netbox, alerts in grouped_alerts.items()
        if netbox
    )
    return [record for record in records if record.downtime > timedelta(0)]


def get_interface_records(start, end, exclude_maintenance=False):
    alerts = get_alert_periods_by_type(start, end, 'linkState', ['linkDown'])
    grouped_alerts = group_by_subject(alerts, Interface)
    return [
        create_record(subject, alerts, start, end)
        for subject, alerts in grouped_alerts.items()
        if subject
    ]


def get_alert_periods_by_type(period_start, period_end, event_type_id, alert_type_ids):
    """Returns AlertHistory objects of a specific event type, overlapping with
    a given time period.

    The AlertHistory objects will be augmented with the attributes
    `start_within` and `end_within`, which represent the intersection of (
    `period_start`, `period_end`) and (`start_time`, `end_time`) (for proper
    calculation of which duration of earch AlertHistory object is inside the
    specified time period.

    """
    return AlertHistory.objects.raw(
        """
    WITH period AS (
  SELECT
    %s AS "start",
    %s AS "end"
)
SELECT
  alerthist.*,
  GREATEST("start", start_time) AS start_within,
  LEAST("end", end_time) AS end_within
FROM alerthist
JOIN period ON ((start_time, end_time) OVERLAPS ("start", "end"))
JOIN alerttype USING (alerttypeid)
WHERE
  alerthist.eventtypeid = %s
  AND end_time IS NOT NULL
  AND alerttype IN %s
ORDER BY netboxid, subid, start_time
    """,
        [period_start, period_end, event_type_id, tuple(alert_type_ids)],
    )
