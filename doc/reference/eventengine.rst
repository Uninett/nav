============
Event Engine
============

Introduction
============

The :program:`Event Engine` is the backend process used by NAV to process the
*event queue*. Whenever a NAV subsystem posts an event to the queue, the
:program:`Event Engine` will pick it up and decide what do to with it.

Typically, the :program:`Event Engine` will generate an alert from the event,
or it may ignore the event entirely, depending on the circumstances. In some
cases, it will delay the alert for a grace period, while waiting for another
corresponding event to resolve the pending problem.


Plugins
=======

Most of the work of the :program:`Event Engine` is done by event handler
plugins from the :py:mod:`nav.eventengine.plugins` namespace. Each event picked
from the queue will be offered to each of the plugins, until one of them
decides to handle the event. If no plugins wanted to handle the event, the
:program:`Event Engine` will perform a very simple default routine to translate
the event directly into an alert (possibly using alert hints given in the event
itself).


Configuration
=============

The operation of the :program:`Event Engine` can be customized using
configuration options in :file:`eventengine.conf`. Most of the configuration
concerns itself with configuring the grace periods (timeouts) for various types
of alerts. The default configuration looks somewhat like this:

.. literalinclude:: ../../python/nav/etc/eventengine.conf
   :language: ini


Exporting alerts from NAV into other systems
============================================

The :program:`Event Engine` can be made to export a stream of alerts. By
setting the ``script`` option in the ``[export]`` section of
:file:`eventengine.conf` to the path of an executable program or script, the
:program:`Event Engine` will start that program and feed a continuous stream of
JSON blobs. describing the alerts it generates, to that programs ``STDIN``.

Alert JSON format
-----------------

The :program:`Event Engine` will export each alert as a discrete JSON
structure. The receiving script will therefore need to be able to parse the
beginning and end of each such object as it arrives. Each object will be
separated by a newline, but no guarantees are made that the JSON blobs
themselves will not also contain newlines.

.. tip::

   Here is a `Stack Overflow comment describing how Python's existing JSON library
   can be used to decode arbitrarily big strings of "stacked" JSON
   <https://stackoverflow.com/questions/27907633/multiple-json-objects-in-one-file-extract-by-python/50384432#50384432>`_,
   such as is the case with the the alert export stream.


An exported alert may look like this as JSON:

.. code-block:: json

   {
      "id" : 212310,
      "history" : 196179,
      "time" : "2019-11-05T10:03:10.235877",
      "message" : "box down example-sw.example.org 10.0.1.42",
      "source" : "pping",
      "state" : "s",
      "on_maintenance" : false,
      "netbox" : 138,
      "device_groups" : null,
      "device" : null,
      "subid" : "",
      "subject_type" : "Netbox",
      "subject" : "example-sw.example.org",
      "subject_url" : "/ipdevinfo/example-sw.example.org/",
      "alert_details_url" : "/api/alert/196179/",
      "netbox_history_url" : "/devicehistory/history/%3Fnetbox=138",
      "event_history_url" : "/devicehistory/history/?eventtype=e_boxState",
      "event_type" : {
         "description" : "Tells us whether a network-unit is down or up.",
         "id" : "boxState"
      },
      "alert_type" : {
         "description" : "Box declared down.",
         "name" : "boxDown"
      },
      "severity" : 50,
      "value" : 100
   }

Attributes explained
~~~~~~~~~~~~~~~~~~~~

These are the attributes present in the JSON blob describing an alert:

``id``
  The internal integer ID of this alert in NAV. This number is volatile, as the
  alert object disappears from NAV as soon as the :program:`Alert Engine` has
  completed its processing of the alert.

``history``
  The internal integer ID of NAV's corresponding alert history entry. I.e., if
  this alert created a new problem state in NAV, this will be a new ID. If this
  alert resolves or otherwise concerns an existing state in NAV, this will
  refer to the pre-existing history ID.

  E.g. if a ``boxDown`` alert is issued for an IP device, and later, a
  ``boxUp`` alert is issued for the same IP device, both of these alerts will
  refer to the same alert history entry.

``time``
  This is the timestamp of the alert, in ISO8601 format. Usually, this
  corresponds to the timestamp of the originating event. E.g., for ``boxState``
  type alerts, this corresponds to the exact timestamp the :program:`pping`
  program reported it could no longer receive ICMP echo replies from a device.
  
``message``
  This is a short, human-readable description of what the alert is all about.
  
``source``
  This is a reference to the NAV subsystem that postged the original event that
  caused this alert.
  
``state``
  This is NAV's internal moniker for the state represented by this alert:
  
  ``x``
    This is a stateless alert (e.g. a generic warning or point-in-time event)
  ``s``
    This alert starts a new state in the alert history table.
  ``e``
    This alert ends (resolves) an existing state in the alert history table.

``on_maintenance``
  A boolean that tells you whether the subject of this alert is currently on
  active maintenance, according to NAV's schedule. This would typically be
  used to withhold notifications about alerts that occur during a known
  maintenance period for a device.
  
``netbox``
  A database primary key to the IP device this alert is associated with.
  
``device_groups``
  A list of NAV device groups that the associated IP device is a member of.
  
``device``
  A database primary key to the physical device this alert is associated with.
  
``subid``
  If this alert's subject is a sub-component of the IP device referenced in the
  ``netbox`` attribute, this will be some internal sub-ID of this
  component. This reference ID can be interpreted differently, depending on the
  alert type, which is what NAV does when the ``subject`` attribute described
  below is composed.
  
``subject``
  An object that describes the alert's actual subject (or object, if you will,
  since NAV's terminology is grammatically challenged).

``subject_type``
  NAV's internal model name of the subject's data type. This would typically be
  things like ``Netbox``, ``Interface``, ``Module``, ``GatewayPeerSession``
  etc.

  A ``subject_type`` value combined with the ``subid`` value can be used as a
  unique identifier of a NAV component by a 3rd party tool.

``subject_url``
  A relative canonical URI to a NAV web page (meant for human consumption)
  describing the alert's subject.
  
``alert_details_url``
  A relative canonical URI to NAV's REST API, where the details of the alert
  state entry can be retrieved.

``netbox_history_url``
  A relative canonical URI to a NAV web page (meant for human consumption)
  detailing the recent alert history of this alert's associated IP device.

``event_history_url``
  A relative canonical URI to a NAV web page (meant for human consumption)
  detailing the recent history of alerts of the same event type (e.g. all the
  recent alerts of the ``boxState`` category, if this is a ``boxDown`` alert).

``event_type``
  A sub-structure describing the event category of this alert:

  ``id``
    The event category id of this alert.
  ``description``
    A description of said event category.

``alert_type``
  A sub-structure describing the alert type of this alert.

  ``id``
    The event type id of this alert.
  ``description``
    A description of said alert type.

``severity``
  The severity of this alert. This is usually an integer in the range *0-100*,
  but at the moment, this carries no specific meaning in NAV.
  
``value``
  The alert value. This is usually an integer in the range *0-100*, but at the
  moment, this carries no specific meaning in NAV.



