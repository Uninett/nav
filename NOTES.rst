=================================================
 Network Administration Visualized release notes
=================================================

Please report bugs at https://bugs.launchpad.net/nav/+filebug . To browse
existing bug reports, go to https://bugs.launchpad.net/nav .

If you are upgrading from versions of NAV older than 3.7, please refer to the
release notes of the in-between versions before reading any further.


Known problems
==============

The recommended SNMP library for use with ipdevpoll is `pynetsnmp`.  If you
choose to go with the original TwistedSNMP, the latest version (0.3.13)
contains a bug that manifests in table retrieval operations.  Timeouts and
retries aren't handled properly, and this may cause slow or otherwise busy
devices to be bombarded with requests from NAV.  The `contrib/patches`
directory contains a patch for TwistedSNMP that solves this problem.  The
patch has been submitted upstream, but not yet accepted into a new release.

NAV 3.14
========

To see the overview of scheduled features and reported bugs on the 3.14 series
of NAV, please go to https://launchpad.net/nav/3.14 .

Dependency changes
------------------

- The `pynetsnmp` library is still optional (for the time being), but is
  **required** if IPv6 support is needed.

Files to remove
---------------

If any of the following files and directories are still in your installation
after upgrading to NAV 3.14, they should be removed (installation prefix has
been stripped from these file names).  If you installed and upgraded NAV using
a packaging system, you should be able to safely ignore this section::

  etc/rrdviewer/
  lib/python/nav/statemon/checker/*.descr
  share/htdocs/js/portadmin.js


NAV 3.13
========

To see the overview of scheduled features and reported bugs on the 3.13 series
of NAV, please go to https://launchpad.net/nav/3.13 .

Dependency changes
------------------

- NAV no longer requires Java. Consequently, the PostgreSQL JDBC driver is no
  longer needed either.
- To use the new `netbiostracker` system, the program ``nbtscan`` must be
  installed.

New eventengine
---------------

The `eventengine` was rewritten in Python. The beta version does not yet
support a config file, but this will come.

There is now a single log file for the `eventengine`, the lower-cased
``eventengine.log``. The ``eventEngine.log`` log file and the ``eventEngine``
log directory can safely be removed.

New alert message template system
---------------------------------

As a consequence of the `eventEngine` rewrite, alert message templates are no
longer stored in the ``alertmsg.conf`` file. Instead, `Django templates`_ are
used as the basis of alert message templates, and each template is stored in
an event/alert hierarchy below the ``alertmsg/`` directory.

Also, NAV 3.13 no longer provides Norwegian translations of these templates.

The hierarchy/naming conventions in the ``alertmsg/`` directory are as follows::

  <event type>/<alert type>-<medium>.[<language>.]txt

The `<event type>` is one of the available event types in NAV, whereas `<alert
type>` is one of the alert types associated with the event type. `<medium>` is
one of the supported alert mediums, such as `email`, `sms` or `jabber`. A two
letter language code is optional; if omitted, English will be assumed.

To make a Norwegian translation of the ``boxState/boxDown-email.txt``
template, copy the file to ``boxState/boxDown-email.no.txt`` and translate the
text inside the copied file.

Variables available in the template context include:

* `source`
* `device`
* `netbox`
* `subid`
* `time`
* `event_type`
* `alert_type`
* `state`
* `value`
* `severity`

Some of these, such as the `netbox` variable, are Django models, and will
enable access to query related information in the NAV database. Various
attributes accessible through the `netbox` variable include:

* `netbox.sysname`
* `netbox.room`
* `netbox.room.location`
* `netbox.category`
* `netbox.organization`

Also, since `Django templates`_ are used, you have the full power of its
template tag library to control and customize the appearance of an alert
message based on the available variables.

.. `_Django templates`: https://docs.djangoproject.com/en/1.2/ref/templates/

VLANs
-----

It is now possible to search for VLANs in the navbar search. The search triggers
on VLAN numbers and netidents.

The VLAN page contains details about the VLAN and its related router ports and
prefixes. The information is linked to the more extensive reports for each
port and prefix.

The page also contains graphs of the number of hosts on the VLAN over time
(both IPv4 and IPv6 hosts, as well as number of unique MAC addresses seen).
Historic information is easily accessible by utilizing the buttons next to the
graphs.

Bootstrapping host count graphs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Collection of the number of active hosts on each VLAN starts as you upgrade to
NAV 3.13. The graphs will therefore have no information prior to this point.

The source information comes from NAV's logs of ARP and ND caches from your
routers. If you upgraded to 3.13 from a previous version, you can bootstrap
your graphs with historical information from NAV's database.

To do this, use the ``collect_active_ip.py`` program provided with NAV 3.13::

  Usage: collect_active_ip.py [options]

  Options:
    -h, --help            show this help message and exit
    -d DAYS, --days=DAYS  Days back in time to start collecting from
    -r, --reset           Delete existing rrd-files. Use it with --days to
                          refill

To bootstrap your graphs with data from the last year (this may take a while),
run::

  sudo -u navcron collect_active_ip.py -d 365 -r

.. NOTE:: NAV does not have historical information about prefixes. If your
          subnet allocations have changed considerably recently, you shouldn't
          bootstrap your graphs further back than this if you want your graphs
          to be as close to the truth as possible.


Arnold
------

Arnold was rewritten to not use ``mod_python`` and to use Django's ORM for
database access. The rewrite has tried to be as transparent as possible and at
the same time fix any open bugs reports.

Some changes are introduced:

- The shell script for interacting directly with Arnold is gone. If there is an
  outcry for it, it will be reintroduced. The other scripts for automatic
  detentions and pursuit are a part of the core functionality and are of course
  still present.

- The workflow when manually detaining has been slightly improved.

- The reasons used for automatic detentions are no longer available when
  manually detaining. This is done to be able to differ between manual and
  automatic detentions. If you detain for the same reason both manually and
  automatically, just create two similar reasons.

- Log levels are no longer set in ``arnold.conf``. Use ``logging.conf`` to
  alter loglevels for the scripts and web.

- Some unreported bugs are fixed.

- The “Open on move”-option in a predefined detention was never used. This is
  fixed.

- Pursuing was not done in some cases.

- Reported bugs that were fixed:
  - LP#341703 Manual detention does not pursue client
  - LP#361530 Predefined detention does not exponentially increase detentions
  - LP#744932 Arnold should give warning if snmp write is not configured

Files to remove
---------------

If any of the following files and directories are still in your installation
after upgrading to NAV 3.13, they should be removed (installation prefix has
been stripped from these file names).  If you installed and upgraded NAV using
a packaging system, you should be able to safely ignore this section::

  bin/arnold.py
  bin/eventEngine.sh
  etc/alertmsg.conf
  etc/eventEngine.conf (new config format in lowercase eventengine.conf)
  lib/java/
  lib/python/nav/web/arnoldhandler.py
  lib/python/nav/web/loggerhandler.py
  lib/python/nav/web/radius/radius.py
  lib/python/nav/web/report/handler.py
  var/log/eventEngine/


NAV 3.12
========

To see the overview of scheduled features and reported bugs on the 3.12 series
of NAV, please go to https://launchpad.net/nav/3.12 .

Dependency changes
------------------

- Python >= 2.6 is now required. NAV will not work under Python 3.
- Django >= 1.2 is now required. NAV will likely not work under Django 1.4.


Cricket configuration
---------------------

Your subtree-sets configuration for Cricket must be updated. This file is most
likely placed in /etc/cricket/. Compare manually with or copy from
`doc/cricket/cricket/subtree-sets`.

Take note of `$(NAV)/etc/mcc.conf`. Module `interfaces` should be there instead
of `routerinterfaces` and `switchports`.

IPv6 statistics for router interfaces will now be collected. For this to work
you need to copy some configuration templates to your `cricket-config`
directory.  NB: Make sure the `dataDir` is the same as the original after
copying the `Defaults` file. If your NAV is installed in `/usr/local/nav`, run
these commands::

  sudo cp doc/cricket/cricket-config/Defaults \
             /usr/local/nav/etc/cricket-config/

  sudo cp -r doc/cricket/cricket-config/ipv6-interfaces \
             /usr/local/nav/etc/cricket-config/

Room map
--------

If you have registered coordinates (latitude, longitude) on your rooms you may
include a geographical map of the rooms on the front page by editing
`etc/webfront/welcome-registered.txt` and/or `welcome-anonymous.txt` and
adding the following HTML::

  <div id="mapwrapper">
      <div id="room_map" class="smallmap"></div>
  </div>

If you feel like having a bigger map, replace `smallmap` with `bigmap`. The
markers are clickable and will take you to the new "Room view" for the clicked
room.

Toolbar search
--------------

The toolbar search now searches for more than IP devices. Try it!

Files to remove
---------------

If any of the following files and directories are still in your installation
after upgrading to NAV 3.12, they should be removed (installation prefix has
been stripped from these file names).  If you installed and upgraded NAV using
a packaging system, you should be able to safely ignore this section::

  doc/getting-started.txt
  doc/mailin/README
  doc/radius/
  etc/apache/subsystems/maintenance.conf
  etc/apache/subsystems/messages.conf
  etc/apache/subsystems/netmap.conf
  lib/python/nav/ipdevpoll/plugins/lastupdated.py
  lib/python/nav/web/maintenance/handler.py
  lib/python/nav/web/messages/handler.py
  lib/python/nav/web/netmap/datacollector.py
  share/htdocs/js/DeviceBrowserTemplate.js
  share/htdocs/js/devicehistory.js
  share/htdocs/js/EditTemplate.js
  share/htdocs/js/ipdevinfo.js
  share/htdocs/js/jquery-1.4.4.min.js
  share/htdocs/js/jquery-json-2.2.min.js
  share/htdocs/js/quickselect.js
  share/htdocs/js/seeddb.js
  share/htdocs/js/seeddbTemplate.js
  share/htdocs/netmap/


NAV 3.11
========

To see the overview of scheduled features and reported bugs on the 3.11 series
of NAV, please go to https://launchpad.net/nav/3.11 .

Dependency changes
------------------

- `JavaSNMP` is no longer a dependency and can be removed. There is also
  therefore no longer any need to export a `CLASS_PATH` variable before
  building NAV from source.

Topology source data
--------------------

The getBoksMacs Java program has been replaced by a set of ipdevpoll plugins,
configured to run under the `topo` job in 15 minute intervals. This job will
collect switch forwarding tables (CAM), STP blocking status, CDP (Cisco
Discovery Protocol) neighbor information and also LLDP (Link Layer Discovery
Protocol) neighbor information.

The navtopology program will now prefer LLDP source information over CDP and
CDP source information over CAM source information when building NAV's
topology.

Unrecognized neighbors from CDP or LLDP are _not_ stored yet by NAV 3.11.0,
but this will be reimplemented in the 3.11 series.


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
