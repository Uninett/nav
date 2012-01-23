=================================================
 Network Administration Visualized release notes
=================================================

Please report bugs at https://bugs.launchpad.net/nav/+filebug . To browse
existing bug reports, go to https://bugs.launchpad.net/nav .

If you are upgrading from versions of NAV older than 3.7, please refer to the
release notes of the in-between versions before reading any further.


Known problems
==============

The latest TwistedSNMP version (0.3.13) contains a bug that manifests in table
retrieval operations.  Timeouts and retries aren't handled properly, and this
may cause slow or otherwise busy devices to be bombarded with requests from
NAV.  The `contrib/patches` directory contains a patch for TwistedSNMP that
solves this problem.  The patch has been submitted upstream, but not yet
accepted into a new release.  Alternatively, you can install `pynetsnmp` for
improved performance.

NAV 3.10
========

To see the overview of scheduled features and reported bugs on the 3.10 series
of NAV, please go to https://launchpad.net/nav/3.10 .

Cricket configuration changes
-----------------------------

NAV 3.10 now configures Cricket to collect a wide range of available sensor
data from devices, including temperature sensors. Devices that implement
either ENTITY-SENSOR-MIB (RFC 3433), CISCO-ENVMON-MIB or IT-WATCHDOGS-MIB (IT
Watchdogs WeatherGoose) are supported.

Your need to copy the baseline Cricket configuration for sensors to your
cricket-config directory. Given that your NAV install prefix is
`/usr/local/nav/`::

  sudo cp -r doc/cricket/cricket-config/sensors \
             /usr/local/nav/etc/cricket-config/

You also need to add the `/sensors` tree to your Cricket's `subtree-sets`
file. See the example file containing all NAV subtrees at
`doc/cricket/cricket/subtree-sets`.

Topology detection
------------------

VLAN subtopology detection has now also been rewritten as a separate option to
the `navtopology` program. The old `networkDiscovery` service has been renamed
to `topology` and now runs physical and vlan topology detection using
`navtopology` once an hour.

If you notice topology problems that weren't there before the upgrade to 3.10,
please report them so that we can fix them.

The old detector code is deprecated, but if you wish to temporarily go back
to the old detector code, you can; see the comments in the `cron.d/topology`
file. The old detector will be removed entirely in NAV 3.11.


Link state monitoring
---------------------

ipdevpoll will now post `linkState` events when a port's link state changes,
regardless of whether you have configured your devices to send link state
traps to NAV.

To avoid a deluge of `linkDown` or `linkUp` alerts from all access ports in
your network, it is recommended to keep the `filter` setting in the
`[linkstate]` section of `ipdevpoll.conf` to the default setting of
`topology`. This means that events will only be posted for ports that have
been detected as uplinks or downlinks.

To facilitate faster detection of link state changes, ipdevpoll is now
configured with a `linkcheck` job that runs the `linkstate` plugin every five
minutes. You can adjust this to your own liking in `ipdevpoll.conf`.

SNMP agent monitoring
---------------------

An `snmpAgentDown` alert will now be sent if an IP device with a configured
community stops responding to SNMP requests.  The ipdevpoll job `snmpcheck`
will check for this every 30 minutes.

To receive alerts about SNMP agent states, please subscribe to
`snmpAgentState` events in your alert profile.


Redundant power supply and fan state monitoring
-----------------------------------------------

NAV now finds and stores information about power supply and fan units from
Cisco and HP devices, and monitors for any failures in redundant
configurations.

For the time being, the monitoring is run by a separate program,
`powersupplywatch.py`, which is by default set up to run as a cron job once an
hour. To adjust the monitoring interval, edit `cron.d/psuwatch`.


IPv6 status monitoring
----------------------

pping has gained support for pinging IPv6 hosts. _However_, SNMP over IPv6 is
not supported quite yet. This means you can add servers with IPv6 addresses
using SeedDB, but not with an enabled SNMP community.

Files to remove
---------------

If any of the following files and directories are still in your installation
after upgrading to NAV 3.10, they should be removed (installation prefix has
been stripped from these file names).  If you installed and upgraded NAV using
a packaging system, you should be able to safely ignore this section::

  doc/sql/*.sql
  etc/cron.d/networkDiscovery
  lib/python/nav/database.py
  lib/python/nav/mcc/routers.py
  lib/python/nav/mcc/switches.py
  lib/python/nav/web/templates/seeddbTemplate.py
  lib/python/nav/web/templates/selectTreeTemplate.py
  lib/python/nav/web/l2trace.py
  lib/python/nav/web/sortedStats.py
  lib/python/nav/web/netmap/handler.py
  lib/python/nav/web/serviceHelper.py
  lib/python/nav/web/ldapAuth.py
  lib/python/nav/web/selectTree.py
  lib/python/nav/statemon/output.py
  lib/templates/geomap/geomap-data-kml.xml
  apache/
  bin/navschema.py


NAV 3.9
=======

To see the overview of scheduled features and reported bugs on the 3.9 series
of NAV, please go to https://launchpad.net/nav/3.9 .


Dependency changes
------------------

- A dependency to the Python library NetworkX (http://networkx.lanl.gov/),
  version 1.0 or newer, has been introduced in the new topology
  detector.

  NetworkX lists a number of optional third party packages that will extend
  NetworkX' functionality, but none of these are currently needed by NAV.

- An optional, but recommended, dependency to the `pynetsnmp` library has been
  introduced to increase SNMP-related performance in the `ipdevpoll` daemon.
  `pynetsnmp` is a ctypes binding (as opposed to a native C module) enabling
  integration with the efficient SNMP processing of the mature NetSNMP
  library.

  `pynetsnmp` was created for and is distributed with ZenOSS.  There doesn't
  seem to be a separate tarball for `pynetsnmp`, but the source code
  repository is at http://dev.zenoss.com/trac/browser/trunk/pynetsnmp . The
  library has been packaged for Debian under the name `python-pynetsnmp`.



NAV 3.8
=======

Source code directory layout
----------------------------
The source code directory layout has changed.  All subystems in the
`subsystems` directory were merged in several top-level directories:

`python`
  All the Python libraries have moved here.

`java`
  All the Java code has moved here.

`bin`
  All executables have been moved here.

`etc`
  All initial/example configuration files have been moved here.

`media`
  All static media files to be served by Apache have moved here.

`templates`
  All Django templates used by NAV have moved here.

`sql`
  All the database schema initialization/migration related files have moved
  here.


Apache configuration
--------------------
NAV's preferred way of configuring Apache has changed.  The default target
directory for an Apache DocumentRoot has therefore also changed, to
`${prefix}/share/htdocs`.

NAV 3.8 only installs static media files into this directory - all Python code
is now kept in NAV's Python library directory.  For Cricket integration,
Cricket's CGI scripts and static media should still be installed in the
DocumentRoot under a separate `cricket` directory (or aliased to the /cricket
location).

NAV now provides its own basic Apache configuration file to be included in
your VirtualHost setup.  This file is installed as
`${sysconfdir}/apache/apache.conf`.  See the `Configuring Apache` section in
the INSTALL file for more details.


Database installation and migration
-----------------------------------
NAV 3.8 introduces an automatic database schema upgrade program.  Every time
you upgrade NAV, all you need to do to ensure your database schema is updated
is to run the `sql/syncdb.py` program.

This program will use the settings from `db.conf` to connect to the NAV
database.  It can also be used to create a NAV database from scratch.


PortAdmin
---------

NAV can now configure switch port descriptions and native VLANs from the IP
Device Info tool, provided that you have set an SNMP write community in
SeedDB (which is also necessary for the Arnold tool to work).

This functionality supports Cisco devices through proprietary MIBs.  Devices
from other vendors are supported as long as they properly implement the
Q-BRIDGE-MIB (RFC 2674) - This has been successfully tested on HP switches.
Alcatel switches seem to block write access to the necessary Q-BRIDGE objects;
we are still looking into this.

Please do not forget to secure your SNMP v2c communications using best
practices.  Limit SNMP communication with your devices to only the necessary
IP addresses or ranges using access lists or similar techniques.  You don't
want users on your network to sniff SNMP community strings and start
configuring your devices, do you?


Dependency changes
------------------

The INSTALL file used to refer to the python package `egenix-mxdatetime` as a
dependency.  This has been removed, as NAV stopped using it in version 3.6.
You psycopg2 installation may still require it, though.

NAV 3.8 also adds a dependency to the Python library `simplejson`.

Also, don't forget: The following dependencies changed from version 3.6 to
3.7:

* Python >= 2.5.0
* PostgreSQL >= 8.3
