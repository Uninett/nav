==================
NAV API Parameters
==================

Here you will find documentation about each endpoint in NAVs API.


Searches
========

On some endpoints you can do searches. This is done by using the search
parameter::

  api/netbox?search=some-sw

The list of fields used in the search are defined for each endpoint. Searches
are case-insensitive and do partial matches.


Filters
=======

Almost all endpoints supports filtering. This is done by specifying a value for
the field you want to filter on::

  api/netbox?room=a-room
  api/netbox?category=GSW


Detailed endpoint specifications
================================


api/alert/
----------

Provides access to NAVs alert status. This is the same as viewing NAV status

:Search: None

:Filters: event_type, not_event_type, organization, not_organization,
           category, not_category, alert_type, not_alert_type,
           device_group, not_device_group

:Additional parameters:
  - ``acknowledged=on`` -  also list acknowledged alerts
  - ``on_maintenance=on`` - also list alerts regarding subjects on maintenance
  - ``stateless=on`` - also list stateless alerts (from the last 24 hours)
  - ``stateless_threshold=<hours>`` - adjust stateless interval



api/arp/[<id>]
--------------

Provides access to NAVs ARP data

:Search: None

:Filters: ip, mac, netbox, prefix

:Additional parameters:
  - active=on - list only entries that are active now (end_time = infinity)


api/cam/[<id>]
--------------

Provides access to NAVs CAM data

:Search: None

:Filters: mac, netbox, ifindex, port

:Additional parameters:
  - active=on - list only entries that are active now (end_time = infinity)


api/interface/[<id>]
--------------------

Provides access to NAVs interface data

:Search: ifalias, ifdescr, ifname

:Filters: ifname, ifindex, ifoperstatus, netbox, trunk, ifadminstatus, iftype,
          baseport


api/netbox/[<id>]
-----------------

Provides access to NAVs netbox data

:Search: sysname

:Filters: ip, sysname, room, organization, category


api/room/[<id>]
---------------

Provides access to NAVs room data

:Search: None

:Filters: location, description


api/prefix/[<id>]
-----------------

Provides access to NAVs prefix data

:Search: None

:Filters: vlan, net_address, vlan__vlan, contains_address

    .. NOTE:: The vlan__vlan is used to filter on vlan number as the vlan field
              references the primary key only.
              e.g. :kbd:`prefix?vlan__vlan=<vlan-number>`


api/prefix/routed
-----------------

List all prefixes that are routed

:Search: None

:Filters: None

:Additional parameters:
  - ``family=<4|6>`` - List only prefixes within the specified family


api/prefix/usage/[<prefix>]
---------------------------

List usage statistics for prefixes. This fetches the number of active
IP-addresses for each prefix and compares it to the number of possible addresses
on each prefix. If no time interval is specified, fetches the current status

:Search: None

:Filters: None

:Additional parameters:
  - ``start_time=<iso8601>`` - set start time
  - ``end_time=<iso8601>`` - set end time


api/unrecognized-neighbors/[<id>]
---------------------------------

Provide access to NAVs unrecognized neighbor data.

:Search: remote_name

:Filters: netbox, source
