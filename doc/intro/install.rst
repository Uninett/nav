================
 Installing NAV
================

.. highlight:: sh

NAV releases official Debian packages. We recommend using these if you can. If
you can't, or won't, please read on.

Install from source on
======================

See :doc:`/howto/manual-install-on-debian` for more complete, Debian-centric
guide to installation of a full NAV system from source.


Dependencies
============

This section specifies what software packages are needed to build and run NAV.
Be aware that many of these packages have dependencies of their own.

Build requirements
------------------

To build NAV, you need at least the following:

 * Python >= 2.7.0 < 3
 * Sphinx >= 1.0 (for building this documentation)

Runtime requirements
--------------------

To run NAV, these software packages are required:

 * Apache2 + mod_wsgi (or, really, any web server that supports the WSGI interface)
 * PostgreSQL >= 9.4 (With the ``hstore`` extension available)
 * Graphite_
 * Python >= 2.7.0
 * nbtscan = 1.5.1
 * dhcping (only needed if using DHCP service monitor)

PostgreSQL and Graphite are services that do not necessarily need to run on
the same server as NAV.

The required Python modules can be installed either from your OS package
manager, or from the Python Package Index (PyPI_) using the regular ``setup.py``
method described below. The packages can also be installed from PyPI_ in a
separate step, using the pip_ tool and the provided requirements files::

  pip install -r requirements.txt

*However*, some of the required modules are C extensions that will require the
presence of some C libraries to be correctly built (unless PyPI provides binary
wheels for your platform). These include the ``psycopg2`` driver and the
``python-ldap`` and ``Pillow`` modules).

The current Python requirements are as follows:

.. literalinclude:: ../../requirements/django18.txt
   :language: text

.. literalinclude:: ../../requirements/base.txt
   :language: text

.. _Graphite: http://graphiteapp.org/
.. _pip: https://pip.pypa.io/en/stable/
.. _PyPi: https://pypi.org/

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

To build and install NAV and all its Python dependencies::

  pip install -r requirements.txt .

This will build and install NAV in the default system-wide directories for your
system. If you wish to customize the install locations, please consult the
output of ``python setup.py install --help``.


.. _initializing-the-configuration-files:

Initializing the configuration
------------------------------

NAV will look for its configuration files in various locations on your file
system. These locations can be listed by running::

  nav config path

To install a set of pristine NAV configuration files into one of these locations,
e.g. in :file:`/etc/nav`, run::

  nav config install /etc/nav

To verify that NAV can find its main configuration file, run::

  nav config where


Initializing the database
-------------------------

Before NAV can run, the database schema must be installed in your PostgreSQL
server.  NAV can create a database user and a database schema for you.

Choose a password for your NAV database user and set this in the ``userpw_nav``
in the :file:`db.conf` config file. As the ``postgres`` superuser, run the following
command::

  navsyncdb -c

This will attempt to create a new database user, a new database and initialize
it with NAV's schema.


Configuring the web interface
-----------------------------

NAV's web interface is implemented using the Django framework, and can be
served in any web server environment supported by Django (chiefly, any
environment that supports *WSGI*). This guide is primarily concerned with
Apache 2.

An example configuration file for Apache2 is provided the configuration
directory, :file:`apache/apache.conf.example`. This configuration uses
``mod_wsgi`` to serve the NAV web application, and can be modified to suit your
installation paths. Once complete, it can be included in your virtualhost
config, which needn't contain much more than this:

.. code-block:: apacheconf

  ServerName nav.example.org
  ServerAdmin webmaster@example.org

  Include /path/to/your/nav/apache.conf

.. important:: You should always protect your NAV web site using SSL!

Installing static resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~

You want your web server to be able to serve all of NAV's static resources. You
can install all of them by issuing the following command:

.. code-block:: console

  # django-admin collectstatic --settings=nav.django.settings
  You have requested to collect static files at the destination
  location as specified in your settings:

      /usr/share/nav/www/static

  This will overwrite existing files!
  Are you sure you want to do this?

  Type 'yes' to continue, or 'no' to cancel:

In this example, type :kbd:`yes`, hit :kbd:`Enter`, and ensure your web server's
document root points to :file:`/usr/share/nav/www`, because that is where the
:file:`static` directory is located. If that doesn't suit you, you will at
least need an Alias to point the ``/static`` URL to the :file:`static`
directory.

Users and privileges
--------------------

Apart from the ``pping`` and ``snmptrapd`` daemons, no NAV processes should
ever be run as ``root``. You should create a non-privileged system user and
group, and ensure the ``NAV_USER`` option in :file:`nav.conf` is set
accordingly. Also make sure this user has permissions to write to the directories
configured in ``PID_DIR``, ``LOG_DIR`` and ``UPLOAD_DIR``.

.. note:: The ``pping`` and ``snmptrapd`` daemons must be started as ``root``
          to be able to create privileged communication sockets. Both daemons
          will drop privileges and run as the configured non-privileged user as
          soon as the sockets have been acquired.

Building the documentation
--------------------------

If you wish, this HTML documentation can be built separately using this step::

  python setup.py build_sphinx

The resulting files will typically be placed in :file:`build/sphinx/html/`.

If you want to serve this documentation on your NAV web server, you should copy
the :file:`html` directory to a suitable location and make sure that location is served
as ``/doc`` on the web server.  If using the example Apache configuration
(:file:`apache.conf.example`), there is a define named ``documentation_path``,
which can be set to point to this file system location.


.. _integrating-graphite-with-nav:

Integrating Graphite with NAV
-----------------------------

.. highlight:: ini

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

Installing Graphite_ itself is out of scope for this guide, but you will need
to configure some options before letting NAV send data to Graphite.

1. First and foremost, you will need to enable the UDP listener in the
   configuration file :file:`carbon.conf`.

   For performance reasons, Carbon will also limit the number of new Whisper
   files that can be created per minute. This number is fairly low by default,
   and when starting NAV for the first time, it may send a ton of new metrics
   very fast. If the limit is set to 50, it will take a long time before all
   the metrics are created. You might want to increase the
   ``MAX_CREATES_PER_MINUTE`` option, or temporarily set it to ``inf``.

2. You should add the suggested *storage-schema* configurations for the
   various ``nav`` prefixes listed in :file:`etc/graphite/storage-schemas.conf`:

   .. literalinclude:: ../../python/nav/etc/graphite/storage-schemas.conf

   The highest precision retention archives are the most important ones here,
   as their data point interval must correspond with the collection intervals
   of various NAV processes. Other than that, the retention periods and the
   precision of any other archive can be freely experimented with.

   Remember, these schemas apply to new Whisper files as they are created. You
   should not start NAV until the schemas have been configured, otherwise the
   Whisper files will be created with the global Graphite defaults, and your
   data may be munged or inaccurate, and your graphs will be spotty.

3. You should add the suggested *storage-aggregation* configurations listed in
   the file :file:`etc/graphite/storage-aggregation.conf`:

   .. literalinclude:: ../../python/nav/etc/graphite/storage-aggregation.conf

   These will ensure that time-series data sent to Graphite by NAV will be
   aggregated properly when Graphite rolls them into lower-precision archives.
