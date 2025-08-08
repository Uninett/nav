======================================
Command line utilities provided in NAV
======================================

.. highlight:: sh

In addition to various daemon and cron job programs, NAV provides some useful
command line utilities to control NAV or work with NAV data.


--------------
:command:`nav`
--------------

:command:`nav` is the most central program to control NAV's background
processes and cron jobs, regardless of whether you are running under SysV init
system, systemd or other process control systems.

If NAV doesn't appear to be doing anything, the first order of business is
checking the state of its background processes with the command
:code:`nav status`


Usage
~~~~~
.. program-output:: nav --help



--------------------------
:command:`navcheckservice`
--------------------------

This utility can be used to test :program:`servicemon` checker plugins against
arbitrary hosts (i.e. not necessarily registered in NAV).

Usage
~~~~~
.. program-output:: navcheckservice --help

Available handler plugins
~~~~~~~~~~~~~~~~~~~~~~~~~

These handler plugins are currently available from :program:`servicemon`:

.. program-output:: python3 -c 'from nav.statemon import checkermap; checkermap.parsedir(); print("\n".join(sorted(checkermap.checkers.keys())))'


----------------
:command:`navdf`
----------------

This command is useful to generate lists of devices registered in NAV. Used
without arguments, it will print out the sysname of every NAV-registered
device.

It is mostly a programmers interface to filtering the device list: It takes an
argument that must be valid Python code and a valid Django QuerySet filtering
function, and therefore requires a bit of knowledge about how the NAV database
is modeled in the Django ORM.

Please refer to the `Django QuerySet documentation
<https://docs.djangoproject.com/en/4.2/ref/models/querysets/>`_ for more
information about how to build filters.


Usage
~~~~~
.. program-output:: navdf --help

Recipes
~~~~~~~

List only GSW and GW category devices::

  navdf "filter(category__id__in=(('GW', 'GSW')))"

List only Juniper devices::

  navdf "filter(type__vendor__id='juniper')"

List only Cisco switches::

  navdf "filter(type__vendor__id='cisco', category_id__in=(('SW', 'EDGE')))"

List only switches in the room *101*::

  navdf "filter(room__id='101', category_id__in=(('SW', 'EDGE')))"


------------------
:command:`navdump`
------------------

This command can dump SeedDB data into CSV text files, which can later be
re-imported in another NAV instance's SeedDB bulk import feature.

Typical usage patterns are described in the :doc:`data migration howto
<migrate-data>`.

Usage
~~~~~
.. program-output:: navdump --help


--------------------
:command:`naventity`
--------------------

This SNMP-specific utility can query the contents of a NAV-registered device's
``ENTITY-MIB::entPhysicalTable`` and output the entity hierarchy to the
terminal. This is a useful way of discovering what a device is actually
reporting about its physical contents to NAV, or if it even supports this
standard mechanism.

The ``ENTITY-MIB`` is defined by the `IETF RFC 6933
<https://datatracker.ietf.org/doc/rfc6933/>`_, and is the primary way NAV
learns about the pysical innards of a network device.


Usage
~~~~~
.. program-output:: naventity --help

-----------------------
:command:`navoidverify`
-----------------------

This command is useful for simple SNMP MIB conformance testing of
NAV-registered devices *in bulk*.

It takes an SNMP OID as its only argument, and a list of NAV-registered device
name in its standard input: It then runs SNMP ``GET-NEXT`` commands for the
given OID against all the listed devices (using the SNMP credentials stored in
NAV), testing to see whether the device response is from within a subtree of
the requested OID. Any device that responds with a value from the subtree will
have its name printed back to the standard output.

Usage
~~~~~
.. program-output:: navoidverify --help

Recipes
~~~~~~~

Let's say you are interested in figuring which of your devices support the
``CISCO-VLAN-MEMBERSHIP-MIB::vmMembershipSummaryTable`` object. First, you need
the full OID of this object, and then you can test it against all your devices
thus (by also utiliziing the :command:`navdf` command mentioned above):

.. code-block:: console

  $ snmptranslate -On CISCO-VLAN-MEMBERSHIP-MIB::vmMembershipSummaryTable
  .1.3.6.1.4.1.9.9.68.1.2.1
  $ navdf | navoidverify .1.3.6.1.4.1.9.9.68.1.2.1
  example-cisco-sw1.example.org
  example-cisco-sw2.example.org
  ...



--------------------
:command:`navpgdump`
--------------------

This command can aid in dumping all or parts of the NAV PostgreSQL database
into a text format (raw SQL commands) suitable for restoring on a different
PostgreSQL server or NAV instance.

If a full dump/restore cycle is needed, you may be better off using the command
line tools provided by your PostgreSQL distribution itself, but if you want to
apply NAV-specific filtering to the data, this command is useful.

In particular, this command is used by NAV developers to do partial dumps of
production data and load these into a development installation for
testing/debugging and development of new features.

Typical usage patterns are described in the :doc:`data migration howto
<migrate-data>`.

Usage
~~~~~
.. program-output:: navpgdump --help

------------------
:command:`navsnmp`
------------------

This little utility is useful when you want to use NET-SNMP command line
utilities to talk to your NAV-registered network devices.

Supply a NAV-registered device's name as its argument, and it will output the
device's SNMP credentials (as stored in NAV, if any) as valid NET-SNMP command
line options. In this way, you don't need to remember which SNMP version,
community or IP address a device has - you only need to remember the first part
of its name.

Usage
~~~~~
.. program-output:: navsnmp --help


Recipes
~~~~~~~

To walk the ``ENTITY-MIB::entPhysicalTable`` table of
``example-sw.example.org``::

  snmpwalk $(navsnmp example-sw) ENTITY-MIB::entPhysicalTable


--------------------
:command:`navsyncdb`
--------------------

This is the central command line utility to create the NAV database schema in
PostgreSQL and keep the schema in sync when upgrading to newer NAV versions.

Run with the correct privileges, it can both create the database user and the
database before initializing the schema, or even drop an exsting NAV database
completely if you want to start from scratch.

Its usage is described in most of the available installation guides. When
installing NAV from Debian packages, you rarely need to interact with this
command, though.

Usage
~~~~~
.. program-output:: navsyncdb --help

-----------------------
:command:`navsynctypes`
-----------------------

If you manage multiple NAV instances, this useful utility can assist you in
making sure your device type registry is kept in sync between instances. It may
be tedious to use SeedDB to manually assign proper names and descriptions for
all the device types auto-created by ipdevpoll during the course of its run,
but if you manage multiple NAV instances, you don't want to have to repeat
these manual steps.

When run on NAV instance **A**, his command line utility outputs to its
standard output a set of SQL commands that can be run on NAV instance **B**'s
PostgreSQL server to ensure that NAV instance **B** has at least all the same
device types as instance **A**, with the same descriptions etc.


Usage
~~~~~
.. program-output:: navsynctypes --help

.. _navuser-usage:
------------------
:command:`navuser`
------------------

This commands interacts with the NAV web interface's user registry, enabling
you to use the command line to add new user accounts, set account passwords,
lock/unlock accounts or give admin privileges to select accounts.

Usage
~~~~~
.. program-output:: navuser --help
