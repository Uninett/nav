Event- and alert type hierarchy
===============================

NAV events and alerts are organized into a type hierarchy. While NAV's backend
monitoring processes usually generate events, the :program:`Event Engine` is
responsible for deciding what to do with those events. In most cases, events
are translated into a corresponding alert by the :program:`Event Engine`.

Most alerts are *stateful*, i.e. they can be viewed as an incident that has a
start time and an end time. If the end time is set to an infinite value, the
alert is considered unresolved (also known as *open*).

Some alert types indicate the beginning of a new alert state, while some alert
types indicate the closure of an existing alert state. E.g. for ``boxState``
alerts, a ``boxDown`` alert indicates that a new stateful incident has occured:
A device is no longer responsive. On the other hand, a ``boxUp`` alert will
cause an existing ``boxState``-type alert to be resolved.


All legal event- and alert-types are registered in the NAV database (and can
thus be extended, even by the user, if need be). The following are the event-
and alert types that come pre-defined with NAV:



*boxState* events
-----------------
Tells us whether a network-unit is down or up.

.. list-table:: Alerts associated with boxState events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``boxDownWarning``
     - Warning sent before declaring the box down.
   * - ``boxShadowWarning``
     - Warning sent before declaring the box in shadow.
   * - ``boxDown``
     - Box declared down.
   * - ``boxUp``
     - Box declared up.
   * - ``boxShadow``
     - Box declared down, but is in shadow.
   * - ``boxSunny``
     - Box declared up from a previous shadow state.




*serviceState* events
---------------------
Tells us whether a service on a server is up or down.

.. list-table:: Alerts associated with serviceState events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``httpDown``
     - http service not responding.
   * - ``httpUp``
     - http service responding.




*moduleState* events
--------------------
Tells us whether a module in a device is working or not.

.. list-table:: Alerts associated with moduleState events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``moduleDownWarning``
     - Warning sent before declaring the module down.
   * - ``moduleDown``
     - Module declared down.
   * - ``moduleUp``
     - Module declared up.




*thresholdState* events
-----------------------
Tells us whether the load has passed a certain threshold.

.. list-table:: Alerts associated with thresholdState events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``exceededThreshold``
     - Threshold exceeded.
   * - ``belowThreshold``
     - Value below threshold.




*linkState* events
------------------
Tells us whether a link is up or down.

.. list-table:: Alerts associated with linkState events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description




*boxRestart* events
-------------------
Tells us that a network-unit has done a restart

.. list-table:: Alerts associated with boxRestart events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``coldStart``
     - The IP device has coldstarted
   * - ``warmStart``
     - The IP device has warmstarted




*info* events
-------------
Basic information

.. list-table:: Alerts associated with info events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``dnsMismatch``
     - Mismatch between sysname and dnsname.
   * - ``serialChanged``
     - Serial number for the device has changed.
   * - ``macWarning``
     - Mac appeared on port




*notification* events
---------------------
Notification event, typically between NAV systems

.. list-table:: Alerts associated with notification events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description




*deviceActive* events
---------------------
Lifetime event for a device

.. list-table:: Alerts associated with deviceActive events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description




*deviceState* events
--------------------
Registers the state of a device

.. list-table:: Alerts associated with deviceState events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``deviceInIPOperation``
     - The device is now in operation with an active IP address.
   * - ``deviceInStack``
     - The device is now in operation as a chassis module.
   * - ``deviceRMA``
     - RMA event for device.
   * - ``deviceNewModule``
     -  The device has been found as a module.
   * - ``deviceNewChassis``
     - The device has been found as a chassis.
   * - ``deviceNewPsu``
     - The device has been found as a power supply.
   * - ``deviceNewFan``
     - The device has been found as a fan.



*deviceNotice* events
---------------------
Registers a notice on a device

.. list-table:: Alerts associated with deviceNotice events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``deviceError``
     - Error situation on device.
   * - ``deviceSwUpgrade``
     - Software upgrade on device.
   * - ``deviceHwUpgrade``
     - Hardware upgrade on device.
   * - ``deviceFwUpgrade``
     - Firmware upgrade on device.




*maintenanceState* events
-------------------------
Tells us if something is set on maintenance

.. list-table:: Alerts associated with maintenanceState events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``onMaintenance``
     - Box put on maintenance.
   * - ``offMaintenance``
     - Box taken off maintenance.




*apState* events
----------------
Tells us whether an access point has disassociated or associated from the controller

.. list-table:: Alerts associated with apState events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``apUp``
     - AP associated with controller
   * - ``apDown``
     - AP disassociated from controller




*snmpAgentState* events
-----------------------
Tells us whether the SNMP agent on a device is down or up.

.. list-table:: Alerts associated with snmpAgentState events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``snmpAgentDown``
     - SNMP agent is down or unreachable due to misconfiguration.
   * - ``snmpAgentUp``
     - SNMP agent is up.




*chassisState* events
---------------------
The state of this chassis has changed

.. list-table:: Alerts associated with chassisState events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``chassisDown``
     - This chassis is no longer visible in the stack
   * - ``chassisUp``
     - This chassis is visible in the stack again




*aggregateLinkState* events
---------------------------
The state of this aggregated link changed

.. list-table:: Alerts associated with aggregateLinkState events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``linkDegraded``
     - This aggregate link has been degraded
   * - ``linkRestored``
     - This aggregate link has been restored




*psuState* events
-----------------
Reports state changes in power supply units

.. list-table:: Alerts associated with psuState events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``psuNotOK``
     - A PSU has entered a non-OK state
   * - ``psuOK``
     - A PSU has returned to an OK state




*fanState* events
-----------------
Reports state changes in fan units

.. list-table:: Alerts associated with fanState events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``fanNotOK``
     - A fan unit has entered a non-OK state
   * - ``fanOK``
     - A fan unit has returned to an OK state




*bgpState* events
-----------------
The state of this BGP peering session changed

.. list-table:: Alerts associated with bgpState events
   :widths: 25 75
   :header-rows: 1

   * - Alert type name
     - Description
   * - ``bgpDown``
     - This BGP peering session is down
   * - ``bgpEstablished``
     - This BGP peering session has been established
   * - ``bgpAdmDown``
     - This BGP peering session is administratively down




