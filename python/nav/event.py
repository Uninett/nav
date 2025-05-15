#
# Copyright (C) 2018 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Simple API to interface with NAVs event queue."""

from django.db import transaction

import nav.db
from nav.errors import GeneralException

from nav.models.event import EventType, AlertType

DEFAULT_SEVERITY = 3


class Event(dict):
    """Represents a single event on or off the queue.

    Use like a dictionary to manipulate event variables (in eventqvar).
    Otherwise, this is just a dumb storage class (any database activity
    performed by this class is done using the EventQ class as proxy)
    """

    def __init__(
        self,
        source=None,
        target=None,
        deviceid=None,
        netboxid=None,
        subid=None,
        time=None,
        eventtypeid=None,
        state=None,
        value=None,
        severity=DEFAULT_SEVERITY,
    ):
        super(Event, self).__init__()
        self.eventqid = None

        self.source = source
        self.target = target
        self.deviceid = deviceid
        self.netboxid = netboxid
        self.subid = subid
        self.time = time
        self.eventtypeid = eventtypeid
        self.state = state
        self.value = value
        self.severity = severity

    def __repr__(self):
        attr_list = [
            "%s=%s" % (attr, getattr(self, attr))
            for attr in (
                'eventqid',
                'source',
                'target',
                'deviceid',
                'netboxid',
                'subid',
                'time',
                'eventtypeid',
                'state',
                'value',
                'severity',
            )
            if getattr(self, attr)
        ]
        attr_list = ", ".join(attr_list)
        return "<Event %s / %s>" % (attr_list, super(Event, self).__repr__())

    def post(self):
        """Post this event to the eventq"""
        return EventQ.post_event(self)

    def delete(self):
        """Delete this event from the event queue

        This should normally only be done when an event has been consumed and
        processed by its target.
        """
        if not self.eventqid:
            raise EventNotPostedError(
                "source=%s, target=%s, type=%s"
                % (self.source, self.target, self.eventtypeid)
            )
        else:
            result = EventQ.delete_event(self.eventqid)
            self.eventqid = None
            return result

    # Alias the delete member function as dispose
    dispose = delete


class EventQ(object):
    """Static class to manipulate the event queue"""

    @classmethod
    def _get_connection(cls):
        conn = nav.db.getConnection('default', 'manage')
        # Make sure the connection doesn't autocommit: Posting an event
        # consists of several SQL statements that should go into a single
        # transaction.
        conn.set_isolation_level(1)
        return conn

    @classmethod
    def allocate_id(cls):
        sql = "SELECT NEXTVAL('eventq_eventqid_seq')"
        conn = cls._get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        if cursor.rowcount > 0:
            return cursor.fetchone()[0]
        else:
            raise EventIdAllocationError

    @classmethod
    def post_event(cls, event):
        if event.eventqid:
            raise EventAlreadyPostedError(event.eventqid)

        # First post the relevant fields to eventq
        fields = []
        values = []
        for attr in (
            'source',
            'target',
            'deviceid',
            'netboxid',
            'subid',
            'time',
            'eventtypeid',
            'state',
            'value',
            'severity',
        ):
            if getattr(event, attr, None):
                fields.append(attr)
                values.append(getattr(event, attr))
        if not fields:
            raise EventIncompleteError
        field_string = ','.join(fields)
        placeholders = ', %s' * len(values)
        eventsql = (
            "INSERT INTO eventq (eventqid, " + field_string + ") "
            "VALUES (%s" + placeholders + ")"
        )
        eventqid = cls.allocate_id()
        conn = cls._get_connection()
        cursor = conn.cursor()
        cursor.execute(eventsql, (eventqid,) + tuple(values))

        # Prepare an SQL statement to post the variables, if any
        if event:
            varsql = "INSERT INTO eventqvar (eventqid, var, val)VALUES (%s, %s, %s)"
            values = [(eventqid,) + i for i in event.items()]
            cursor.executemany(varsql, values)

        # If we got this far, commit the transaction and update the event
        # object with the allocated id

        conn.commit()
        event.eventqid = eventqid
        return cursor.statusmessage

    @classmethod
    def consume_events(cls, target):
        """Consume and return a list of Event objects queued for this target.

        Events that are processed should be deleted from the queue afterwards.
        """
        eventsql = """SELECT eventqid, source, target, deviceid, netboxid,
                             subid, time, eventtypeid, state, value, severity
                      FROM eventq
                      WHERE target = %s"""
        conn = cls._get_connection()
        conn.commit()
        cursor = conn.cursor()

        def load_vars(event):
            varsql = "SELECT var, val FROM eventqvar WHERE eventqid=%s"
            curs = conn.cursor()
            curs.execute(varsql, (event.eventqid,))
            if curs.rowcount > 0:
                for var, val in curs.fetchmany():
                    event[var] = val

        events = []
        cursor.execute(eventsql, (target,))
        if cursor.rowcount > 0:
            for event_row in cursor.fetchall():
                event = Event()
                (
                    event.eventqid,
                    event.source,
                    event.target,
                    event.deviceid,
                    event.netboxid,
                    event.subid,
                    event.time,
                    event.eventtypeid,
                    event.state,
                    event.value,
                    event.severity,
                ) = event_row
                load_vars(event)
                events.append(event)
        return events

    @classmethod
    def delete_event(cls, eventqid):
        """Delete the event with the specified id from the queue.

        This should normally only be done when an event has been consumed and
        processed by its target.
        """
        sql = "DELETE FROM eventq WHERE eventqid = %s"
        conn = cls._get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (eventqid,))
        conn.commit()
        return cursor.statusmessage


class EventIdAllocationError(GeneralException):
    """Error allocating a new event ID from the queue"""

    pass


class EventAlreadyPostedError(GeneralException):
    """Event was already posted"""

    pass


class EventIncompleteError(GeneralException):
    """Incomplete event cannot be posted"""

    pass


class EventNotPostedError(GeneralException):
    """Cannot perform this operation on an unposted event"""

    pass


@transaction.atomic
def create_type_hierarchy(hierarchy):
    """Create an event/alert type hierarchy in the database.

    If the hierarchy already exists, nothing is done.

    hierarchy -- A structure like this:
      { (event_type_name, description, stateful) :
        [(alert_type_name, description), ...]
      }

    Returns: The number of objects created.  A return value of 0
    indicates that all the objects already exist.

    This function uses the Django ORM for database access, thus it is
    not async-safe.

    Usage example:

    >>> h = {('apState', 'Access point assocation/disassociation events', True):
    ...      [('apUp', 'AP associated with controller'),
    ...       ('apDown', 'AP disassociated from controller'),
    ...      ]}
    >>> create_type_hierarchy(h)
    3
    >>>

    """
    created_count = 0

    for event_type, alert_types in hierarchy.items():
        event_type_name, event_descr, stateful = event_type
        if stateful not in ('y', 'n'):
            # Parse the stateful var as a boolean
            stateful = 'y' if stateful else 'n'

        try:
            etype = EventType.objects.get(id=event_type_name)
        except EventType.DoesNotExist:
            etype = EventType(
                id=event_type_name, description=event_descr, stateful=stateful
            )
            etype.save()
            created_count += 1

        for alert_type_name, alert_descr in alert_types:
            atype, created = AlertType.objects.get_or_create(
                name=alert_type_name, event_type=etype
            )
            if created:
                atype.description = alert_descr
                atype.save()
                created_count += 1

    return created_count
