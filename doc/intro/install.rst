================
 Installing NAV
================

.. highlight:: sh

Dependencies
============

This section specifies what software packages are needed to build and run NAV.
Be aware that many of these packages have dependencies of their own.

Build requirements
------------------

To build NAV, you need at least the following:

 * make
 * automake
 * autoconf
 * Python >= 2.7.0
 * Sphinx >= 1.0 (for building this documentation)
 * A `sass` compiler (to build the NAV web interface's stylesheets. Installing
   the rubygem `sass` would satisfy this requirement)

Runtime requirements
--------------------

To run NAV, these software packages are required:

 * Apache2
 * mod_wsgi
 * PostgreSQL >= 9.1
 * Graphite (http://graphite.wikidot.com)
 * Python >= 2.7.0
 * nbtscan = 1.5.1
 * dhcping (only needed if using DHCP service monitor)

PostgreSQL and Graphite are services that do not necessarily need to run on
the same server as NAV.

The following Python modules are required:

 * :mod:`django` >= 1.2
 * :mod:`IPy` >= 0.70
 * :mod:`ldap` >= 2.3
 * :mod:`networkx` >= 1.1
 * :mod:`psycopg2` >= 2.2
 * :mod:`pyrad`
 * :mod:`rrd` (from the rrdtool distribution)
 * :mod:`simplejson` >= 2.0.6
 * :mod:`twisted` >= 10.1
 * :mod:`pynetsnmp` (or less preferably, :mod:`pysnmp-se` combined with :mod:`twistedsnmp` >= 0.3)
 * :mod:`PIL` >= 1.1.7 (python-imaging)
 * :mod:`django-oauth2-provider` >= 0.2.6
 * :mod:`djangorestframework` >= 2.3.7
 * :mod:`iso8601`

The following python modules are optional:

 * :mod:`xmpp` (optional)

.. tip:: NAV comes with a :file:`requirements.txt` file that can be used in
         conjunction with `pip` to install all the Python dependencies 
         using :kbd:`pip install -r requirements.txt`. This file is also likely to
         be more up-to-date for development versions than this install
         document.

.. note:: The :mod:`pynetsnmp` module is preferred over :mod:`twistedsnmp` for
          SNMP communication. The former is a Python binding to the well-known
          NetSNMP C library, whereas the latter is a pure-Python SNMP
          implementation. :mod:`pynetsnmp` will give better performance *and*
          IPv6-support. :mod:`twistedsnmp` also has a known, unfixed bug with
          table retrievals on slow SNMP agents. If, for some reason, you are
          forced to resort to using :mod:`twistedsnmp`, the :file:`contrib/patches`
          directory contains a recommended patch for this problem.


Recommended add-ons
-------------------

If you want to connect a mobile phone to your NAV server and enable SMS alerts
in alert profiles, you will need to install :program:`Gammu` and the Python
:mod:`gammu` module.  The SMS daemon can use plugins to dispatch text
messages through other means, but using Gammu as an SMS dispatcher is the
default.

If you wish to use the Jabber plugin for alertengine, the python module :mod:`xmpp`
is required.


Installing NAV
==============

To build and install NAV::

  ./configure
  make
  make install

.. NOTE:: If you obtained your copy of NAV directly from a Mercurial
          repository, you may need to run ``./autogen.sh`` first.

If you wish to configure NAV to run from a different location than the default
:file:`/usr/local/nav` you should specify a new directory using the
`--prefix=` option of the configure script, e.g. ``./configure
--prefix=/opt/nav``.

If you are building an RPM package (or similar) of NAV, you may wish to have
the files installed in a physically different location (a temporary build
directory) than what you configured the package for.  In this case, you should
specify this build directory by adding
``DESTDIR=/your/build/directory`` to the ``make install`` command.


Initializing the database
-------------------------

Before NAV can run, the database schema must be installed in your PostgreSQL
server.  NAV can create a database user and a database schema for you.  

Choose a password for your NAV database user and set this in the ``userpw_nav``
in the :file:`db.conf` config file. As the `postgres` superuser, run the following
command::

  navsyncdb -c

This will attempt to create a new database user, a new database and initialize
it with NAV's schema.

For more details on setting up PostgreSQL and initializing the schema, please
refer to the :file:`sql/README` file.


Making the Python libraries available system-wide
-------------------------------------------------

By default, NAV's Python libraries are not installed in Python's
:file:`site-packages` directory.  To make them available system-wide, you need
to add the path to the libraries to Python's search path.

One way of accomplishing this is altering Python's ``sys.path`` value at
startup time, by modifying or adding your Python installation's
:file:`sitecustomize.py` module, which is loaded every time python runs.  Add
these lines:

.. code-block:: python

  import sys
  __navpath = "/usr/local/nav/lib/python"
  if __navpath not in sys.path:
      sys.path.append(__navpath)

You should now be able to run the python command line interpreter and run
:kbd:`import nav` without a hitch:

.. code-block:: console

  $ python
  Python 2.7.3 (default, Sep 26 2013, 20:03:06) 
  [GCC 4.6.3] on linux2
  Type "help", "copyright", "credits" or "license" for more information.
  >>> import nav
  >>>

Configuring Apache
------------------

NAV's web interface is implemented using the Django framework,
and can be served in any web server environment supported by Django.

NAV does, however, come with Apache configuration to serve the web interface
using `mod_wsgi`. For legacy reasons, NAV requires being served at the
document root of the web server domain. The apache config file can be
included in your virtualhost config, which needn't contain much more than this:

.. code-block:: apacheconf

  ServerName nav.example.org
  ServerAdmin webmaster@example.org

  Include /usr/local/nav/etc/apache/apache.conf


Create users and groups
-----------------------

NAV processes should run as the `navcron` user (the name of this user is
configurable via the :kbd:`./configure` command at build-time), and
preferably, a separate nav group should be added to the system::

  sudo addgroup --system nav
  sudo adduser --system --no-create-home --home /usr/local/nav \
               --shell /bin/sh --ingroup nav navcron;

If you want to use NAV's SMS functionality in conjunction with Gammu, you
should make sure the `navcron` user is allowed to write to the serial device
you've connected your GSM device to. Often, this device has a group ownership
set to the `dialout` group, so the easieast route is to add the `navcron` user
to the dialout group::

  sudo addgroup navcron dialout

You should also make sure `navcron` has permission to write log files, pid
files and various other state information::

  cd /usr/local/nav/var
  sudo chown -R navcron:nav .


Integrating Graphite with NAV
-----------------------------

NAV uses Graphite to store and retrieve/graph time-series data. NAV must be
configured with the IP address and port of your Graphite installation's Carbon
backend, and the URL to the Graphite-web frontend used for graphing. These
settings can be configured in the :file:`graphite.conf` configuration file.

.. note:: NAV requires the Carbon backend's UDP listener to be enabled, as it
          will only transmit metrics over UDP.

For a simple, local Graphite installation, you may not need to touch this
configuration file at all, but at its simplest it looks like this::

  [carbon]
  host = 127.0.0.1
  port = 2003

  [graphiteweb]
  base = http://localhost:8000/


Configuring Graphite
~~~~~~~~~~~~~~~~~~~~

Installing Graphite itself is out of scope for this guide, but you will need
to configure some options before letting NAV send data to Graphite.

1. First and foremost, you will need to enable the UDP listener in the
   configuration file :file:`carbon.conf`. For performance reasons, Carbon
   will also limit the number of new Whisper files that can be created per
   minute. This number is fairly low by default, and when starting NAV for the
   first time, it may send a ton of new metrics very fast. If the limit is set
   to 50, it will take a long time before all the metrics are created. You
   might want to increase the ``MAX_CREATES_PER_MINUTE`` option, or
   temporarily set it to ``inf``.

2. You should add the suggested *storage-schema* configurations for the
   various NAV prefixes listed in :file:`etc/graphite/storage-schemas.conf`.
   The smallest resolution retention archives are the most important ones
   here, as their resolution must correspond with the collection intervals of
   various NAV processes. Other than that, the retention periods and the
   resolution of any other archive can be freely experimented with.

   Remember, these schemas apply to new Whisper files as they are created. You
   should not start NAV until the schemas have been configured, otherwise the
   Whisper files will be created with the global Graphite defaults, and your
   data may be munged or inaccurate, and your graphs will be spotty.

3. You should add the suggested *storage-aggregation* configurations listed in
   :file:`etc/graphite/storage-aggregation.conf`. These will ensure that
   time-series data sent to Graphite by NAV will be aggregated properly when they
   are rolled into lower-resolution archives.

