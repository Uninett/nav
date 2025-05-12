===================
 Getting organized
===================

NAV offers several ways to organize your seed data and collected information.


Organizing your seed data
=========================

NAV's data model allows you to organize your IP device information in several ways:

* *Define physical or conceptual locations of your operation*. These usually map
  to geographical domains, such as locations for each campus in a multi-campus
  university.

* *Define your rooms, such as server rooms and wiring closets*, where your
  equipment is actually wired up, and organize these into each of your
  locations. Geographical point coordinates can be attached to each room, for
  display on a map.

* *Define an organizational hierarchy*. This can be used to set which
  organizational unit is responsible for the operation of each IP device you
  monitor, and to map your subnets and VLANs to organizational units.

* *Define arbitrary groups of devices*. Some examples: Grouping all your print
  servers, your web servers, or just grouping your most critical routers.
  These groups can later be used for filtering alerts.

All these definitions are entered into NAV through the *SeedDB* tool, where
you added your devices in the :doc:`getting started guide <getting-started>`.
If you already have much of this information in electronic format, it too can
be bulk imported into NAV using the text formats described in each SeedDB tab.

As seen in that guide, NAV ships with an example location, room and
organizational unit. These are fine for just trying things out, but to truly
take advantage of NAV's capabilities and gain control of your network
inventory, you should take spend some time *getting organized*.


Organizing your collected data
==============================

Once your routers and switches are being monitored, NAV will collect
information about your subnets and VLAN assignments, how these relate to each
other, and store them in its database.


VLANs and subnets
-----------------

NAV supports two different conventions for router port descriptions; if
adopted, these allow NAV to categorize each VLAN into a *usage category* and
an owner (an organizational unit from the previously defined hierarchy).

`Read the guidelines in our wiki to learn how to do this
<https://nav.uninett.no/wiki/subnetsandvlans>`_. Usage categories are also defined
using the SeedDB tool.


Network prefixes and scopes
---------------------------

Each network prefix configured in your device's interfaces will be collected
and stored by NAV. To the best of its ability, NAV will correlate which VLAN
corresponds to each prefix. Sometimes, VLANs will have multiple prefixes, in
the case of secondary network addresses or when both IPv4 and IPv6 are
deployed in a subnet.

NAV features a subnet matrix tool which charts your subnet allocations and
their utilization percentages. To take advantage of this, you must manually
add one ore more *scope prefixes* through the SeedDB *Prefix* tab. Each scope
prefix will usually correspond to an IP address block you have been assigned
by your regional internet registry (in some cases, you may want to subdivide
those further, for your own organizational purposes).

You can also add *reserved prefixes* using SeedDB. These are typically
prefixes within your scope that aren't routed by your equipment, but possibly
reserved for third parties or some future use. The subnet matrix tool will
highlight these address ranges accordingly.



Vendors and device types
------------------------

NAV will automatically discover and assign *device types* to SNMP-enabled
devices that are being monitored. Each device type corresponds to a unique
*sysObjectID*. An SNMP-enabled device will usually report a vendor-specific
and unique *sysObjectID*, which may map to some specific device model, type
and/or software.

Each device type in NAV is mapped to a *vendor ID*, a moniker such as
``cisco`` or ``juniper``. You can edit your device types and vendors through
the SeedDB tool.

When NAV sees a previously unknown *sysObjectID* it will automatically
register a new device type and attach it to the ``unknown`` vendor id. You may
wish to later edit these auto-created device types using the SeedDB *Type*
tab to set the correct vendor id and a more proper type name and description.

Vendor OUIs and MAC addresses
-----------------------------

NAV's Machine Tracker search tool allows searching logs of ARP and CAM data
collected from your routers and switches.  It provides an optional OUI vendor
lookup for MAC address results.  The OUI mapping database is populated by the
:program:`navoui` cronjob on a daily basis.  If you're on day 1 with your NAV
install and do not want to wait for the cronjob to run for the first time, you
can run the :program:`navoui` command manually to populate the OUI table
immediately.

Cabling and patching
--------------------

If desireable, you can also document your cabling plans and your patch panels
using SeedDB. This would enable NAV to tell you to which office each switch
port is patched through to (unless you are already diligent and add this
information to the switch port description when patching).
