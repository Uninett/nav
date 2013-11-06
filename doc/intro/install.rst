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
 * PostgreSQL >= 9.1
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
 * :mod:`django-oauth2-provider` >= 0.2.6
 * :mod:`djangorestframework` >= 2.3.7
 * :mod:`iso8601`

The following python modules are optional:

 * :mod:`xmpp` (optional)

.. tip:: NAV comes with a :file:`requirements.txt` file that can be used in
         conjunction with `pip` to install all the Python dependencies using
         :kbd:`pip install -r requirements.txt`. This file is also likely to
         be more up-to-date for development versions than this install
         document.

.. note:: The :mod:`pynetsnmp` module is preferred over :mod:`twistedsnmp` for
          SNMP communication. The former is a Python binding to the well-known
          NetSNMP C library, whereas the latter is a pure-Python SNMP
          implementation. :mod:`pynetsnmp` will give better performance *and*
          IPv6-support. :mod:`twistedsnmp` also has a known, unfixed bug with
          table retrievals on slow SNMP agents. If, for some reason, you are
          forced to resort to using :mod:`twistedsnmp`, the
          :file:`contrib/patches` directory contains a recommended patch for
          this problem.


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

NAV processes should run as the `navcron` user, and preferably, a
separate nav group should be added to the system::

  sudo addgroup --system nav
  sudo adduser --system --no-create-home --home /usr/local/nav \
	       --shell /bin/sh --ingroup nav navcron;

If you want to use NAV's SMS functionality in conjunction with Gammu, you
should make sure the `navcron` user is allowed to write to the serial device
you've connected your GSM device to.  Often, this device has a group ownership
set to the dialout group, so the easieast route is to add the `navcron` user to
the dialout group::

  sudo addgroup navcron dialout

You should also make sure `navcron` has permission to write log files, rrd files
and pid files::

  cd /usr/local/nav/var
  sudo chown -R navcron:nav .


Integrating Graphite with NAV
-----------------------------

.. WARNING:: This needs to be documented! 
