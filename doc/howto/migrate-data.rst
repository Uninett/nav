#####################################################
 Migrating data from one NAV installation to another
#####################################################

This how-to explores two methods of migrating data from one NAV installation
to another, depending on your specific needs.

.. note:: This guide does not cover in detail data stored outside of NAV's
          PostgreSQL database, such as time-series data in Graphite, log
          files, or configuration files.

***************************
What data should I migrate?
***************************

If you want to migrate your entire NAV installation from one server to
another, you should consider these points:

* Uploaded resources, such as room images, are stored in the file system, in
  the :file:`uploads/` directory under NAV's ``localstatedir`` (on Debian,
  this is typically :file:`/var/lib/nav/uploads/`). This directory structure
  can easily be copied to the target host, using your preferred combination of
  :program:`rsync`/:program:`scp`/:program:`tar`.

* Do you run NAV's PostgreSQL server on the same host as NAV itself? If so,
  you should perform a full dump of the PostgreSQL cluster using
  :program:`pg_dumpall` and load this onto the target host.

  If you are an advanced PostgreSQL, you could utilize database replication or
  other strategies to minimize downtime.

* Do you run your Carbon (Graphite) back-end on the same host as NAV? If so,
  you should copy all your Whisper files (where Graphite stores its time
  series data) to the target host, using your preferred combination of
  :program:`rsync`/:program:`scp`/:program:`tar`.

* Don't forget your configuration files! Not only NAV's configuration files,
  but also PostgreSQL and Graphite, if you are migrating those as well.


If you want to migrate only parts of the data, you should read on.

*******************
Migrating seed data
*******************

If you wish to discard your NAV history and establish a new NAV server to
monitor the same set of devices as your old NAV server, migrating your NAV's
seed data should be enough.

Seed data are the data you can enter through the Seed DB tool, consisting
mostly of data NAV needs to start monitoring your network. These do not
contain collected inventory data (except for possibly prefixes and VLANs),
event logs, user accounts or other items.

Migrating this data is a two-step process:

1. Dump the seed data to a set of text files.
2. Bulk import the text files in the receiving installation's SeedDB
   interface.

For dumping seed data to text files, NAV provides the :program:`navdump`
program. To dump all seed data to the current working directory:

.. code-block:: console

  $ navdump  -a
  Dumping vendor.txt
  Dumping room.txt
  Dumping service.txt
  Not smart to use : as separator for services, using ;
  Dumping netbox.txt
  Dumping prefix.txt
  Not smart to use : as separator for prefixes, using ;
  Dumping location.txt
  Dumping usage.txt
  Dumping org.txt
  Dumping type.txt
  Dumping netboxgroup.txt

Each of the dumped files represent data that can be bulk imported in one of
the SeedDB tabs. They usually need to be imported in a specific order, as some
of the data will be inter-dependent. A usable order of import is:

* vendor.txt
* location.txt
* room.txt
* org.txt
* netboxgroup.txt
* type.txt
* netbox.txt
* service.txt
* usage.txt
* prefix.txt

For more information about :ref:`bulk importing in SeedDB
<seeddb-bulk-import-intro>`, see :doc:`../intro/getting-started`.

**************************************
Migrating all or parts of the database
**************************************

Intro
-----

NAV stores most of its data (except time-series data like traffic statistics)
in the PostgreSQL relational database. The contents of this database can be
dumped to a SQL text file, which can be used to create a new, identical NAV
database on the receiving end.

.. tip:: If you just want to backup your entire database, you are likely
         better off using PostgreSQLs own :program:`pg_dumpall` program. This
         will dump all databases in a PostgreSQL data cluster, including the
         users and table access privileges.

NAV features the :program:`navpgdump` program, which can facilitate dumping of
the NAV database while filtering unnecessary or unwanted data. This makes it
ideal for moving parts of your production data to a test installation if you
want to beta test the next NAV release.

Dumping
-------

To just dump the entire contents of the NAV database, you can invoke the
:program:`navpgdump` program. The contents are dumped directly to
:file:`stdout`, so you should redirect to a file::

  navpgdump > nav-data.sql

In a long-running NAV installation, most of the data will be be machinetracker
logs, i.e. timestamped ARP and CAM records from your routers and switches. If
the logs are unneeded on the destination installation, you may wish to keep
only the currently active records. This will *greatly* reduce the size of your
data dump. You can use the `-a` and `-c` options (or their long-form
counterparts) to only dump open ARP and CAM records, respectively::

  navpgdump --only-open-arp --only-open-cam > nav-data.sql

Using the `-e` option, you can exclude the entire contents of selected tables.
This may require knowledge of NAV's data model before you proceed. If you know
your way around SQL, you can even enact more advanced content filters using
the `-f` or `--filter` option.

.. tip:: See the output of :code:`navpgdump --help` for a complete overview of
         the supported options.

Restoring
---------

The :program:`navsyncdb` program, used for creating and updating the NAV
database schema, can also be used to restore a dump created by the
:program:`navpgdump` program.

To create a new NAV database, using the data stored in :file:`nav-data.sql`::

  navsyncdb --create --restore nav-data.sql

Just as creating a new NAV database from scratch, this requires
:file:`db.conf` to be configured properly. You can optionally drop a
pre-existing NAV database using the ``--drop-database`` option to
:program:`navsyncdb`, but **do not use this option on a production system
unless you are willing to lose all your data**.


Full migration to a test server
-------------------------------

If you, for example, have installed a beta version of NAV on a virtual
machine/testing server, and wish to copy most of your production data (but not
your years of machine tracker logs) to it, you can do the full migration in
one single command line on the test server like this::

  ssh production-nav navpgdump --only-open-arp --only-open-cam | \
    navsyncdb --drop-database --create --restore -

This command is repeatable; when run, it will destroy the running test
database and restore the current production data into a new test database.

.. tip:: When using :program:`navsyncdb` to create/restore the database,
         always remember to stop all NAV processes and the Apache web server,
         which may currently be accessing the database. Failure to do so may
         cause :program:`navsyncdb` to stall forver while waiting for the
         other processes to release their locks on the database.

.. _migrating_prod_db_to_dev:

Migrating a production database to a development environment
------------------------------------------------------------

As with the test server example above, for some development tasks, it is useful
to initialize the development database with a database snapshot from a
production server. The :file:`tools/` directory contains shell scripts to
streamline this operation somewhat in a development environment (but they
basically wrap the same commands as mentioned in the previous section):

:file:`tools/dump-remote-db.sh`
    Runs the :program:`navpgdump` program over an *SSH connection* to a remote
    host and dumps the output to ``stdout``, automatically filtering out old
    machine tracker log records and alert profiles (so the development server
    won't attempt to send notifications to real users).  Requires the
    :program:`navpgdump` program to be available on the remote system's
    :envvar:`PATH`. If you need to customize the filters used while dumping, you
    can make your own version of this script.

:file:`tools/restore-db.sh`
    Stops NAV processes, drops the current NAV database and re-initializes it
    with an SQL dump read from ``stdin``.  This program assumes the
    :program:`psql` program is available and that the necessary configuration
    for it to connect to an actual PostgreSQL database are present (such as the
    environment variables :envvar:`PGHOST`, :envvar:`PGPORT`,
    :envvar:`PGDATABASE`, :envvar:`PGUSER`, etc.). In the devcontainer
    environment this should already be set up for you.

:file:`tools/reset-db-from-remote.sh`
    Combines the two previous programs into a single operation, for
    convenience.

Usage examples
~~~~~~~~~~~~~~

.. code-block:: sh
   :caption: Initialize database from remote server ``prefect.example.org``, as user ``ford``

   tools/reset-db-from-remote.sh ford@prefect.example.org


.. code-block:: sh
   :caption: Save a remote database dump to a file and re-use it later

   tools/dump-remote-db.sh ford@prefect.example.org > mydump.sql
   cat mydump.sql | tools/restore-db.sh
