===========================
 Release notes for NAV 3.8
===========================
Please report bugs at https://bugs.launchpad.net/nav

If you are upgrading from versions of NAV older than 3.7, please refer to the
release notes of the in-between versions before reading any further.

Known problems
==============
The latest TwistedSNMP version (0.3.13) contains a bug that manifests in table
retrieval operations.  Timeouts and retries aren't handled properly, and this
may cause slow or otherwise busy devices to be bombarded with requests from
NAV.  The `contrib/patches` directory contains a patch for TwistedSNMP that
solves this problem.  The patch has been submitted upstream, but not yet
accepted into a new release.


To see the overview of scheduled features and reported bugs on the 3.8 series
of NAV, please go to https://launchpad.net/nav/3.8 .


Significant changes since NAV 3.7
=================================

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
The INSTALL file referred to the python package `egenix-mxdatetime` as a
dependency.  This has been removed, as NAV stopped using it in version 3.6.
You psycopg2 installation may still require it, though.

NAV 3.8 also adds a dependency to the Python library `simplejson`.

Also, don't forget: The following dependencies changed from version 3.6 to
3.7:

* Python >= 2.5.0
* PostgreSQL >= 8.3
