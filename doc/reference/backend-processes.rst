==========================
 Backend processes in NAV
==========================

NAV has a number of back-end processes. This page attempts to give an overview
of them.


The nav command
===============

The shell command ``nav list`` lists all back-end processes. ``nav status``
tells you if they are running as they should. With reference to the list, jump
directly to the relevant section in this document:

- `activeip`_
- `alertengine`_
- `eventengine`_
- `ipdevpoll`_
- `logengine`_
- `mactrace`_
- `maintengine`_
- `netbiostracker`_
- `pping`_
- `psuwatch`_
- `servicemon`_
- `smsd`_
- `snmptrapd`_
- `thresholdMon`_
- `topology`_

activeip
--------

Collects active ip-adresses for all prefixes.

This process finds all active IP addresses for all prefixes by querying the
database, and stores the them by sending the data to the configured Carbon instance.
This is done to be able to view history and trends regarding active IP
addresses.

Dependencies
  A working Carbon instance

Run mode
  cron

Configuration
  None

Logging
  - **collect_active_ip.log**


alertengine
-----------

*alertengine* dispatches alerts according to individual alert profiles.

The alert engine processes alerts on the alert queue and checks whether any
users have subscribed to the alert in their active user profile. If so, alert
engine sends the alert to the user on a predefined format set in the
profile.

Alert templates must be defined for alerts to be understandable by the
recipients.

Dependencies
  `eventengine`_ must be running and post alerts to the alert queue. NAV users
  must have set up their profiles. If their are no matches here, *alertengine*
  will simply delete the alerts.

Run mode
  daemon

Configuration
  - **alertengine.conf**
  - alert templates are defined in the directory ``alertmsg``

Logging
  - **alertengine.log**


eventengine
-----------

Reacts and creates alerts from events on the event queue.

The event engine processes events on the event queue and posts alerts on the
alert queue. Event engine has a mechanism to correlate events; i.e. if the
ppinger posts up events right after down events, this will not be sent as
boxDown alerts, only boxDown warnings. Further if a number of boxDown events are
seen, event engine looks at topology and reports boxShadow events for boxes in
shadow of the box being the root cause.

Dependencies
  The various monitors need to post events on the `event queue` (with `target`
  event engine) in order for event engine to have work.

Run mode
  daemon

Configuration
  - **eventengine.conf**

Logging
  - **eventengine.log**


ipdevpoll
---------

Collects SNMP inventory data from IP devices.

More information can be found by reading the :doc:`ipdevpoll` documentation.

Dependencies
  Seed data must be added using the Seed Database tool.

Run mode
  daemon

Configuration
  - **ipdevpoll.conf**

Logging
  - **ipdevpoll.log**

Details
+++++++

jobs and plugins
  All ipdevpoll's work is done by plugins. Plugins are organized into jobs, and
  jobs are scheduled for each active IP device individually.

inventory job
  Polls for inventory information every 6 hours (by default). Inventory
  information includes interfaces, serial numbers, modules, VLANs and prefixes.

profiler job
  Runs every 5 minutes, profiling devices if deemed necessary. NAV has an
  internal list of SNMP OIDs that are tested for compatibility with each
  device. This is used to create a sort of profile that says what the device
  supports - the profile is typically used to produce a Cricket configuration
  that will collect statistics from proprietary OIDs.

logging job
  Runs every 30 minutes and collects log-like information from devices. At the
  time being, only the arp plugin runs, collecting ARP caches from routers. ARP
  data is logged to a table, and aids in topology detection and client machine
  tracking.


logengine
---------

Regularly check the syslog for network messages and update the logger database.

*logengine* analyzes cisco syslog messages from switches and routers and inserts
them in a structured manner in the logger database. This enables using the web
interface for searching and filtering log messages.

Dependencies
  Something must put logs in a file for parsing

Run mode
  cron

Configuration
  - **logger.conf**

Logging
  - Outputs only to STDERR. Error messages will be sent to the email address
    specified in **nav.conf** as *ADMIN_MAIL*.


mactrace
--------

Checks NAV's cam log for watched MAC addresses.

This process tries to find MAC-addresses that are under surveillance and reports
where they are located. To put a MAC-address under surveillance, the *MAC Watch*
tool in the web interface needs to be used.

This process has a misleading name for historical reasons. Previously there
existed a process called *mactrace* that collected cam information from
switches. This process was implemented into `ipdevpoll`_, but for deployment
reasons the file needed to have the same name.

Dependencies
  For this process to be useful, MAC addresses need to be added by using the
  *MAC Watch* tool in the web-interface.

Run mode
  cron

Configuration
  - The configuration of MAC addresses to look for is done in the web interface.

Logging
  - **macwatch.log**


maintengine
-----------

Regularly check the maintenance-queue and post events to eventq.

*maintengine* checks the defined maintenance schedules. If start or end of a
maintenance period occurs at this run time, the relevant maintenance events are
posted on the event queue - one for each IP device and/or service in question.

Dependencies
  NAV users must have set up maintenances for this process to do anything useful.

Run mode
  cron

Configuration
  The configuration of maintenances is done in the web interface.

Logging
  - **maintengine.log**


netbiostracker
--------------

Regularly fetch netbiosnames from active computers.

*netbiostracker* scans IPv4-networks using the ``nbtscan`` program. All results
are stored in the database for use when displaying data about IP addresses.

Dependencies
  The program ``nbtscan`` must be installed

Run mode
  cron

Configuration
  - **netbiostracker.conf**

Logging
  - **netbiostracker.log**

pping
-----

Pings all IP devices for status monitoring.

*pping* monitors all IP devices in the database. It works effectively in
parallel, being able to ping a large number of devices. Has configurable
robustnes criteria for defining when a box actually is down. Results are posted
on the event queue.

.. important:: A host is declared down on the event queue after four consecutive
               “no responses”. This means that it takes between 80 and 99
               seconds from a host is down till pping declares it as down.

               The event engine will have a grace period of one minute before a
               box down warning is posted on the alert queue, and another
               three minutes before the box is declared down.

               **In summery expect 5-6 minutes before a host is declared down.**

Dependencies
  None

Run mode
  daemon

Configuration
  - **pping.conf**

Logging
  - Logs to configurable file, default **pping.log**


psuwatch
--------

Monitors the state of redundant PSUs and fans.

Uses SNMP to query for current state and compares it with the state stored in
the database. Results are posted on the event queue. The event- and alert system
takes care of messaging.

Dependencies
  Supports only HP and Cisco devices

Run mode
  cron

Configuration
  None

Logging
  - **powersupplywatch.log**


servicemon
----------

Monitors configured services.

*servicemon* monitors services on IP devices. It uses plugins to be able to
monitor a number of different services - almost 20 services are currently
supported. Writing custom plugins is also possible - see
:doc:`../hacking/writing-a-servicemon-plugin`.

Each plugin is by default run every minute with a default timeout of five
seconds. After the plugin has reported the service down three times, servicemon
declares it down.

Dependencies
  The service monitor itself has no dependencies, however custom service
  monitors may introduce local dependencies.

Run mode
  daemon

Configuration
  - **servicemon.conf**

Logging
  - **servicemon.conf** has an option for specifying log file that by default is
    set to **servicemon.log**


smsd
----

Dispatches queued SMS alerts.

Checks the database for new messages, formats the messages into one SMS and
dispatches it via one or more dispatchers with a general interface. Support for
multiple dispatchers are handled by a dispatcher handler layer.

Dependencies
  `alertengine`_ must have posted alerts

Run mode
  daemon

Configuration
  - **smsd.conf**

Logging
  - **smsd.log**


snmptrapd
---------

Receives and processes SNMP traps and notifications.

*snmptrapd* listens to port 162 for incoming traps. When the snmptrapd receives
a trap it puts all the information in a trap-object and sends the object to
every traphandler stated in the *traphandlers* option in **snmptrapd.conf**. It
is then up to the traphandler to decide if it wants to process the trap or just
discard it.

Run mode
  daemon

Configuration
   - **snmptrapd.conf**

Logging:
  - **snmptrapd.log**: logs output from the snmptrapd
  - **snmptraps.log**: logs all traps that the snmptrapd has received


thresholdmon
------------

Monitors your Graphite metrics for exceeded thresholds.

For each given threshold rule *thresholdmon* checks if the collected value
surpasses the given threshold. If it does, an event is posted. The event- and
alert system takes care of the notifications.

For thresholds that are already surpassed, a check is done to see if the values
are down to normal. A normal state is by default defined as the inverted of the
alert threshold, but a separate threshold can be defined for the purpose of
avoiding alert flapping [#]_.

Dependencies
  Thresholds to monitor need to be added using the web interface.

Run mode
  cron

Configuration
  All configuration is done using the web interface.

Logging
  - **thresholdmon.log**

.. [#] With *alert flapping* we mean the situation where the monitored value
       oscillates above and below the configured threshold so that a stream of
       up and down alerts are posted.


topology
--------

Detects the topology of your network.

The topology process builds NAV's model of the physical network topology as well
as the VLAN sub-topologies.

Physical topology
+++++++++++++++++

The topology discovery system builds NAV's view of the network topology based on
cues from information collected previously via SNMP.

The information cues come from routers' IPv4 ARP caches and IPv6 Neighbor
Discovery caches, interface physical (MAC) addresses, switch forwarding tables
and CDP (Cisco Discovery Protocol). The mactrace process has already pre-parsed
these cues and created a list of neighbor candidates for each port in the
network.

The physical topology detection algorithm is responsible for reducing the list
of neighbor candidates of each port to just one single device.

In practice the use of CDP makes this process very reliable for the devices
supporting it, and this makes it easier to correctly determine the remaining
topology even in the case of missing information. CDP is, however, not trusted
more than switch forwarding tables, as CDP packets may pass unaltered through
switches that don't support CDP, causing CDP data to be inaccurate.

VLAN topology
+++++++++++++

After the physical topology model of the network has been built, the logical
topology of the VLANs still remains. Since modern switches support 802.1Q
trunking, which can transport several independent VLANs over a single physical
link, the logical topology can be non-trivial and indeed, in practice it usually
is.

The vlan discovery system uses a simple top-down depth-first graph traversal
algorithm to discover which VLANs are actually running on the different trunks
and in which direction. Direction is here defined relative to the router port,
which is the top of the tree, currently owning the lowest gateway IP or the
virtual IP in the case of HSRP. Re-use of VLAN numbers in physicallyq disjoint
parts of the network is supported.

The VLAN topology detector does not currently support mapping unrouted VLANs.

Dependencies
  Needs complete and sane information in the database

Run mode
  cron

Configuration
  None

Logging
  - **navtopology.log**


Other processes
===============

arnold
------

The different processes that define Arnold can be read more about in the
:doc:`Arnold reference documentation <arnold>`.
