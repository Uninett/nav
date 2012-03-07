================
 Installing NAV
================

.. contents:: Table of contents

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
 * ant
 * Python >= 2.5.0
 * Java 2 SDK >= 1.5.0
 * Cheetah Templates >= 2.0rc7

Runtime requirements
--------------------
To run NAV, these software packages are required:

 * Apache2
 * mod_python
 * Cricket
 * PostgreSQL >= 8.3
 * rrdtool
 * Cheetah Templates >= 2.0rc7
 * Java 2 SDK >= 1.5.0
 * Python >= 2.5.0

The following Java librares are required:

 * PostgreSQL JDBC driver

The following python modules are required:

 * django >= 1.0
 * ipy
 * ldap
 * networkx >= 1.0
 * psycopg2
 * pysnmp-se
 * pyrad
 * rrd (from the rrdtool distribution)
 * simplejson
 * twisted >= 8.1
 * twisted-snmp >= 0.3

The following python modules are optional:

 * pynetsnmp (optional)
 * xmpp (optional)

`psycopg2` should be at least version 2.0.8: Earlier versions have bugs that may
cause some NAV programs to crash.

twisted-snmp has a known, unfixed bug with table retrievals on slow SNMP
agents. The `contrib/patches` directory contains a recommended patch for this
problem.


Recommended add-ons
-------------------
If you want to connect a mobile phone to your NAV server and enable SMS alerts
in alert profiles, you will need to install the Gammu and python-gammu
packages.  The SMS damon can use plugins to dispatch SMS'es through other
means, but using Gammu as an SMS dispatcher is the default.

If you wish to use the Jabber plugin for alertengine, the python module xmpp
is required.


Installing NAV
==============
To build and install NAV::

  ./configure CRICKETDIR=/path/to/cricket/binaries
  make
  make install

You may need to run `./autogen.sh` first, if you obtained your copy of NAV
directly from a Mercurial repository.

If you wish to configure NAV to run from a different location than the default
`/usr/local/nav` you should specify a new directory using the `--prefix=`
option of the configure script, e.g. `./configure --prefix=/opt/nav`.

If you are building an RPM package (or similar) of NAV, you may wish to have
the files installed in a physically different location (a temporary build
directory) than what you configured the package for.  In this case, you should
specify this build directory by adding `DESTDIR=/your/build/directory` to the
`make install` command.

If you omit the `CRICKETDIR` variable, which specifies the path to your
Cricket installation's binaries, it will be assumed that these can be found in
`${prefix}/cricket/cricket`, i.e.  `/usr/local/nav/cricket/cricket` if all
default values are unchanged.  A typical value for a Debian install is
`/usr/share/cricket`.


Initializing the database
-------------------------
Before NAV can run, the database schema must be installed in your PostgreSQL
server.  NAV can create a database user and a database schema for you.  

Choose a password for your NAV database user and set this in the `userpw_nav`
in the `db.conf` config file. As the postgres superuser, run the following
command::

  cd sql
  ./syncdb.py -c

This will attempt to create a new database user, a new database and initialize
it with NAV's schema.

For more details on setting up PostgreSQL and initializing the schema, please
refer to the `sql/README` file.


Making the Python libraries available system-wide
-------------------------------------------------
By default, NAV's Python libraries are not installed in Python's
`site-packages` directory.  To make them available system-wide, you need to
add the path to the libraries to Python's search path.

One way of accomplishing this is altering Python's `sys.path` value at startup
time, by modifying or adding your Python installation's `sitecustomize.py`
module, which is loaded every time python runs.  Add these lines::

  import sys
  __navpath = "/usr/local/nav/lib/python"
  if __navpath not in sys.path:
      sys.path.append(__navpath)

You should now be able to run the python command line interpreter and
import nav without a hitch::

  % python
  Python 2.5.2 (r252:60911, Jan 24 2010, 14:53:14)
  [GCC 4.3.2] on linux2
  Type "help", "copyright", "credits" or "license" for more information.
  >>> import nav
  >>>

Making the necessary Java libraries available to NAV
----------------------------------------------------
The fastest way is to symlink the PostgreSQL JDBC driver library to NAV's java
library directory::

  sudo ln -s /usr/share/java/postgresql.jar /usr/local/nav/lib/java/

Configuring Apache
------------------
Legacy parts of NAV uses mod_python, and therefore requires an Apache 2
server.  For the time being, NAV also requires being at the document root of
its own Apache virtualhost.

NAV provides an Apache config file, with the minimum settings required for
getting a NAV virtualhost to work.  This can be included in your virtualhost
config file, which needn't contain much more than this::

  ServerName nav.example.org
  ServerAdmin webmaster@example.org

  Include /usr/local/nav/etc/apache/apache.conf


Create users and groups
-----------------------
NAV processes should run as the navcron user, and preferably, a
separate nav group should be added to the system::

  sudo addgroup --system nav
  sudo adduser --system --no-create-home --home /usr/local/nav \
	       --shell /bin/sh --ingroup nav navcron;

If you want to use NAV's SMS functionality in conjunction with Gammu, you
should make sure the navcron user is allowed to write to the serial device
you've connected your GSM device to.  Often, this device has a group ownership
set to the dialout group, so the easieast route is to add the navcron user to
the dialout group::

  sudo addgroup navcron dialout

You should also make sure navcron has permission to write log files, rrd files
and pid files::

  cd /usr/local/nav/var
  sudo chown -R navcron:nav .


Integrating Cricket with NAV
----------------------------
NAV will automatically create a cricket configuration tree and keep it synced
based on the information retrieved from the monitored devices.

The initial, empty cricket configuration tree that NAV will work on should be
copied from the documentation directory.  The config directory must be
writeable by the navcron user if config updates are to take place::

  sudo cp -r /usr/local/nav/doc/cricket/cricket-config /usr/local/nav/etc/
  sudo chown -R navcron:nav /usr/local/nav/etc/cricket-config

Now you need to locate your cricket-conf.pl file and edit it to tell cricket
where to locate the configuration tree that NAV keeps.  Make sure that::

  $gConfigRoot = "/usr/local/nav/etc/cricket-config"

Also make sure that the navcron user has write permissions to whatever
directory the `$logDir` option points to.

Cricket comes with a file called subtree-sets, which contains some defaults
that will be useless for us.  This file groups parts of the configuration tree
that will collected during the same collect-subtree run.  You should replace
Cricket's default version of this file with
`/usr/local/nav/doc/cricket/cricket/subtree-sets`.

Cricket needs to know where to store its RRD data, we suggest in NAV's var
directory.  Create a suitable directory here::

    sudo mkdir /usr/local/nav/var/cricket-data
    sudo chown navcron /usr/local/nav/var/cricket-data

Now tell Cricket to put the files there, by editing
`/usr/local/nav/etc/cricket-config/Defaults` and making sure that it
contains::

  Target  --default--
      dataDir         = /usr/local/nav/var/cricket-data/%auto-target-path%

You can now have Cricket compile this empty tree to make sure everything works
so far::

  sudo -u navcron cricket-compile

NAV's `mcc.py` program will generate a new version of the configuration tree
every night around 5 am.  You kan manually update the configuration once
you've seeded a bunch of devices into NAV and NAV has found their interfaces,
instead of waiting till 5 am, by issuing the command::

  sudo -u navcron /usr/local/nav/bin/mcc.py


Integrating the Cricket web interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Cricket comes with its own CGI based web interface for browsing the collected
statistics.  To make this interface available under NAV's web pages, you can
symlink Cricket's cgi scripts into a directory under NAV's document root.
Change directories to the one containing cricket's `*.cgi` scripts and run the
following::

  sudo mkdir /usr/local/nav/share/htdocs/cricket
  sudo ln -s $PWD/grapher.cgi /usr/local/nav/share/htdocs/cricket/
  sudo ln -s $PWD/mini-graph.cgi  /usr/local/nav/share/htdocs/cricket/
  cd /usr/local/nav/share/htdocs/cricket
  sudo ln -s grapher.cgi index.cgi
  sudo cp /usr/local/nav/doc/cricket/public_html/cricket.css .

Also, find Cricket's images directory and symlink that as well::

  sudo ln -s $PWD/images /usr/local/nav/share/htdocs/cricket


You should now have a completely installed and integrated NAV. For a guide on
how to get started, please refer to the file `doc/getting-started.txt`.
