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
 * Python >= 2.6.0
 * Sphinx >= 1.0 (for building this documentation)

Runtime requirements
--------------------

To run NAV, these software packages are required:

 * Apache2
 * mod_wsgi
 * Cricket
 * PostgreSQL >= 8.4
 * rrdtool
 * Python >= 2.6.0
 * nbtscan = 1.5.1
 * dhcping (only needed if using DHCP service monitor)


The following python modules are required:

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

The following python modules are optional:

 * :mod:`xmpp` (optional)

The :mod:`pynetsnmp` module is preferred over :mod:`twistedsnmp` for SNMP
communication. The former is a Python binding to the well-known NetSNMP C
library, whereas the latter is a pure-Python SNMP implementation.
:mod:`pynetsnmp` will give better performance *and* IPv6-support.
:mod:`twistedsnmp` also has a known, unfixed bug with table retrievals on slow
SNMP agents. If, for some reason, you are forced to resort to using
:mod:`twistedsnmp`, the :file:`contrib/patches` directory contains a
recommended patch for this problem.


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

  ./configure CRICKETDIR=/path/to/cricket/binaries
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

If you omit the :makevar:`CRICKETDIR` variable, which specifies the path to your
Cricket installation's binaries, it will be assumed that these can be found in
:file:`${prefix}/cricket/cricket`.  A typical value for a Debian install is
:file:``/usr/share/cricket``.


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
  Python 2.6.6 (r266:84292, Dec 27 2010, 00:02:40) 
  [GCC 4.4.5] on linux2
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

NAV processes should run as the |nav_user| user, and preferably, a
separate nav group should be added to the system::

  sudo addgroup --system nav
  sudo adduser --system --no-create-home --home /usr/local/nav \
	       --shell /bin/sh --ingroup nav |nav_user|;

If you want to use NAV's SMS functionality in conjunction with Gammu, you
should make sure the |nav_user| user is allowed to write to the serial device
you've connected your GSM device to.  Often, this device has a group ownership
set to the dialout group, so the easieast route is to add the |nav_user| user to
the dialout group::

  sudo addgroup |nav_user| dialout

You should also make sure |nav_user| has permission to write log files, rrd files
and pid files::

  cd /usr/local/nav/var
  sudo chown -R |nav_user|:nav .


Integrating Cricket with NAV
----------------------------

.. note:: 
   
  When you see the text ``PATH_TO_NAV``, this means you should replace this text
  with the actual path to your NAV installation.

You need to tell :program:`Cricket` where to locate the configuration. Locate
your :file:`cricket-conf.pl` file and edit it. Make sure that it contains the
following:

.. code-block:: perl

  $gConfigRoot = "PATH_TO_NAV/etc/cricket-config"

To test that things work so far, have Cricket compile its configuration::

  sudo -u |nav_user| cricket-compile
  [16-Nov-2012 15:22:22 ] Starting compile: Cricket version 1.0.5 (2004-03-28)
  [16-Nov-2012 15:22:22 ] Config directory is PATH_TO_NAV/etc/cricket-config
  [16-Nov-2012 15:22:23 ] Processed x nodes (in x files) in x seconds.

NAV will generate a new version of the configuration tree every night. You kan
manually generate the configuration (once you've seeded some devices into NAV)
by issuing the command::

  sudo -u |nav_user| PATH_TO_NAV/bin/mcc.py


Integrating the Cricket web interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cricket comes with its own CGI based web interface for browsing the collected
statistics. NAV provides its own front-end to Cricket's CGI script to ensure
access is authenticated and authorized according to NAV's user database.

You will at least need to symlink Cricket's :file:`images` directory into
NAV's :file:`cricket` directory to render the interface properly. Assuming
your Cricket installation's files are all located in
:file:`/usr/share/cricket` (as they are on Debian)::

  cd PATH_TO_NAV/share/htdocs/cricket
  sudo ln -s /usr/share/cricket/images .

You should now have a completely installed and integrated NAV. For a guide on
how to get started using NAV, please refer to the :doc:`getting-started`
tutorial.
