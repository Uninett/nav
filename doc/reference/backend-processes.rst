==========================
 Backend processes in NAV
==========================

NAV has a number of back-end processes. This page attempts to give an overview
of them.


The nav command
===============

The :program:`nav` program is used to start, stop and query the running state
of NAV's backend processes.

:code:`nav list` lists all back-end processes. :code:`nav status` reports their
current running state. With reference to the list, jump directly to the
relevant section in this document:

- `activeip`_
- `alertengine`_
- `dbclean`_
- `emailreports`_
- `eventengine`_
- `ipdevpoll`_
- `logengine`_
- `mactrace`_
- `maintengine`_
- `navoui`_
- `navstats`_
- `netbiostracker`_
- `pping`_
- `servicemon`_
- `smsd`_
- `snmptrapd`_
- `thresholdMon`_
- `topology`_

activeip
--------

This process runs every 30 minutes, summarizing the number of active IP
addresses per prefix, based on data from the NAV database. The numbers are
stored as Graphite metrics, thus enabling the subnet utilization trend graphs,
available pr. prefix or VLAN in the web UI.


:Dependencies:
  A working Carbon instance
:Run mode:
  cron
:Configuration:
  None
:Logs:
  :file:`collect_active_ip.log`


alertengine
-----------

The Alert Engine monitors the alert queue and dispatches alerts according to
the individual users' active alert profiles.

Alert message templates must be defined for alerts to be understandable by the
recipients.

:Dependencies:
  `eventengine`_ must be running and post alerts to the alert queue. NAV users
  must have set up their profiles.
:Run mode:
  daemon
:Configuration:
  - :file:`alertengine.conf`
  - alert templates are defined in the config directory :file:`alertmsg/`
:Logs:
  :file:`alertengine.log`

emailreports
------------

Sends daily/weekly/monthly business report e-mail, according to subscriptions.

For each configured subscription in the :program:`Business Reports` web tool,
this cron job generates and dispatches the actual report e-mails.

:Dependencies:
  Subscriptions must be added using the :program:`Business Reports` web UI
  tool.
:Run mode:
  cron
:Configuration:
  All configuration is done using the web interface.
:Logs:
  None

eventengine
-----------

The Event Engine monitors the event queue, translating new events to alerts,
which are then posted to the alert queue for processing by `alertengine`_.

The Event Engine has mechanisms for correlating and delaying events. For
example, when `pping`_ sends a down event for an IP device, it has a grace
period of about 4 minutes to send a corresponding up event, before the Event
Engine actually posts the alert that declares the IP device as down.

Also, the Event Engine examines the network topology to correlate events from
`pping`_. If an IP device appears to be unreachable because NAV's path to it
passes through another device currently known to be down, a ``boxShadow``
alert will be posted instead of a ``boxDown`` alert.

:Reference:
  :doc:`Event Engine reference guide <eventengine>`
:Dependencies:
  The various monitors need to post events on the *event queue*, targeted at
  ``eventEngine``, in order for the Event Engine to have anything to do.
:Run mode:
  daemon
:Configuration:
  :file:`eventengine.conf`
:Logs:
  :file:`eventengine.log`


dbclean
-------

Regularly cleans out old data from the NAV database, using the
:program:`navclean` program. The standard cleanup routine removes old web user
interface sessions, and deletes IP devices that have been scheduled for
deletion through either SeedDB or the API.  Additionally, it closes open ARP
records that have been collected from routers that have been unreachable for
more than 30 minutes (adjustable by modifying the `dbclean` cron fragment).

:Dependencies:
  None
:Run mode:
  cron
:Configuration:
  None.
:Logs:
  None

ipdevpoll
---------

Collects inventory and status information from IP devices, using SNMP. More
information can be found by reading the :doc:`ipdevpoll` documentation.

:Dependencies:
  Seed data must be added using the Seed Database tool.
:Run mode:
  daemon
:Configuration:
  :file:`ipdevpoll.conf`
:Logs:
  :file:`ipdevpoll.log`


logengine
---------

Monitors a log file for Cisco syslog messages, structuring them and storing
them in the NAV database. These messages are made searchable through the
Syslog Analyzer web UI.

:Dependencies:
  Something, typically a syslog daemon, must put logs in a file for parsing.
:Run mode:
  cron
:Configuration:
  :file:`logger.conf`
:Logs:
  Outputs only to STDERR. Error messages will be sent by the cron daemon to
  the email address specified in the ``ADMIN_MAIL`` option of
  :file:`nav.conf`.


mactrace
--------

Regularly search NAV's CAM log for "watched" MAC addresses, reporting new
matching entries. Use the *MAC Watch* web tool to put MAC addresses under
surveillance.

This process has a misleading name, for historical reasons. Previously, there
existed a process called *mactrace* that collected NAV's CAM logs from
switches. Today, this collection takes place in an `ipdevpoll`_ job, but
for deployment reasons, the file needed to have the same name.

:Dependencies:
  For this process to be useful, MAC addresses need to be added by using the
  *MAC Watch* tool in the web interface.
:Run mode:
  cron
:Configuration:
  None, other than the list of watched addresses entered through the web
  interface.
:Logs:
  :file:`macwatch.log`


maintengine
-----------

Regularly checks the maintenance schedule, enforcing it by dispatching the
appropriate maintenance events for individual devices and services on NAV's
*event queue*.

:Dependencies:
  NAV users must add maintenance tasks to the maintenance schedule for
  this process to do anything useful.
:Run mode:
  cron
:Configuration:
  Maintenance tasks are configured in the web interface.
:Logs:
  :file:`maintengine.log`


navoui
------

Periodically updates the database with Organizationally Unique Identifiers (OUIs)
and their corresponding vendors. This enables NAV to display the vendor name
of a device based on its MAC address, helping to identify whether a device is,
for example, from Juniper or Cisco.

:Dependencies:
  None
:Run mode:
  cron
:Configuration:
  None
:Logs:
  Logs to STDERR.


navstats
--------

Regularly produces Graphite metrics from the configured SQL statements in
:file:`navstats.conf`. By default, SQL reports are configured to log metrics of
the number of difference IP Device types, the number of switch ports, and the
number of switch ports that have an active link. More can be configured by the
user in the config file.

:Dependencies:
  None
:Run mode:
  cron
:Configuration:
  :file:`navstats.conf`
:Logs:
  :file:`maintengine.log`


netbiostracker
--------------

Regularly fetches NetBIOS names from active hosts in your network.

*netbiostracker* scans IPv4 networks, using the ``nbtscan`` program. Results
are searchable through the Machine Tracker tool.

:Dependencies:
  The program ``nbtscan`` must be installed
:Run mode:
  cron
:Configuration:
  :file:`netbiostracker.conf`
:Logs:
  :file:`netbiostracker.log`

pping
-----

Pings all IP devices for status monitoring.

*pping* monitors all IP devices in the database. It works effectively in
parallel, being able to ping a large number of devices. Has configurable
robustness criteria for defining when a box actually is down. Results are
posted on the event queue.

.. important:: A host is declared unresponsive by pping after four consecutive
               packet losses. This means that it takes between 80 and 99
               seconds from a host stops responding until pping posts a
               ``boxState`` event on the *event queue*

               `eventengine`_ will have a grace period of one minute, before a
               ``boxDownWarning`` is posted on the *alert queue*, and another
               three minutes before an actual ``boxDown`` state is declared.

               **In summary, expect 5-6 minutes to pass before a host is declared down.**

:Dependencies:
  None
:Run mode:
  daemon
:Configuration:
  :file:`pping.conf`
:Logs:
  :file:`pping.log` (configurable)


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

:Dependencies:
  The service monitor itself has no dependencies, however custom service
  monitors may introduce local dependencies.
:Run mode:
  daemon
:Configuration:
  :file:`servicemon.conf`
:Logs:
  :file:`servicemon.log` (configurable)


smsd
----

Monitors the SMS message queue, dispatching new messages as they appear.

If there are multiple simultaneous message to the same phone number, smsd
strives to fit as many of them as it can into a single SMS.

smsd supports multiple SMS dispatch methods, implemented as plugins. Multiple
dispatcher plugins can be ordered to facilitate fallback methods when the
primary dispatch methods fail. The recommended dispatcher is based on
`Gammu`_, and requires a mobile phone or other GSM unit attached directly to
the NAV server (typically using its RS232 or USB interfaces).

:Dependencies:
  A running `alertengine`_ to post SMS alerts in the SMS queue.
:Run mode:
  daemon
:Configuration:
  :file:`smsd.conf`
:Logs:
  :file:`smsd.log`


.. _Gammu: http://wammu.eu/gammu/

snmptrapd
---------

Receives and processes SNMP traps and notifications.

*snmptrapd* listens to port 162 for incoming traps. When the snmptrapd receives
a trap, it puts all the information in a trap object and sends the object to
every *trap handler* stated in the ``traphandlers`` option of :file:`snmptrapd.conf`. It
is then up to the *trap handler* to decide if it wants to process the trap or just
discard it.

:Run mode:
  daemon
:Configuration:
   :file:`snmptrapd.conf`
:Logs:
  - :file:`snmptrapd.log`: logs regular log output from the daemon
  - :file:`snmptraps.log`: logs details of all received traps


thresholdmon
------------

Monitors your Graphite metrics for exceeded thresholds.

For each configured threshold rule, *thresholdmon* monitors the associated
Graphite metrics. Any metric that exceeds the threshold configured by the rule
will cause *thresholdmon* to post a threshold start event to the *event
queue*.

A threshold end event is posted when the metric returns to a value below the
set threshold - or, if you want hysteresis (which you probably do), the
threshold rule can also specify an explicit lower threshold value for clearing
the threshold alert.

:Dependencies:
  Threshold rules must be added using the web interface.
:Run mode:
  cron
:Configuration:
  All configuration is done using the web interface.
:Logs:
  :file:`thresholdmon.log`


topology
--------

Detects the topology of your network.

The topology process builds NAV's model of the physical network topology, as well
as the VLAN sub-topologies.

Physical topology
+++++++++++++++++

The topology discovery system builds NAV's view of the network topology based on
cues from information collected previously via SNMP.

The information cues come from routers' IPv4 ARP caches and IPv6 Neighbor
Discovery caches, interface physical (MAC) addresses, switch forwarding tables
and CDP (Cisco Discovery Protocol). These cues are mostly collected by the
`ipdevpoll_` ``topo`` job, which maintains a list of neighbor candidates for
each port in the network.

The physical topology detection algorithm is responsible for reducing the list
of neighbor candidates of each port to just one single device.

In practice, the use of LLDP (and CDP) makes this process very reliable for
the devices supporting it, and this makes it easier to correctly determine the
remaining topology even in the case of missing information.

(However, CDP can be slightly unreliable in a heterogeneous network, as CDP
packets may pass unaltered through switches that don't support CDP. Two Cisco
switches on each end of an HP switch may see each other as directly connected,
while the HP switch between them remains invisible).

VLAN topology
+++++++++++++

After the physical topology model of the network has been built, the logical
topology of the VLANs still remains. Since modern switches support 802.1Q
trunking, which can transport several independent VLANs over a single physical
link, the logical topology can be non-trivial, and indeed, in practice it usually
is.

The VLAN discovery system uses a simple top-down, depth-first graph traversal
algorithm to discover which VLANs are actually running on the different trunks
and in which direction. Direction is here defined relative to the router port,
which is the top of the tree, currently owning the lowest gateway IP or the
virtual IP in the case of HSRP/VRRP. Re-use of VLAN numbers in physically
disjoint parts of the network is supported.

The VLAN topology detector does not currently support mapping unrouted VLANs.

:Dependencies:
  Needs complete and sane information in the database
:Run mode:
  cron
:Configuration:
  None
:Logging:
  :file:`navtopology.log`


Other processes
===============

arnold
------

The different processes that define Arnold can be read more about in the
:doc:`Arnold reference documentation <arnold>`.
