=================================
 Installing NAV from source code
=================================

This is a generic guide to installing NAV from source code on a \*NIX flavored
operating system. The specifics of how to install NAV's dependencies, such as
:xref:`PostgreSQL` or :xref:`Graphite` will be entirely up to you and your choice of OS.
Note that building NAV from source will also require Node.js and npm to be installed
in order to manage frontend assets.


Dependencies
============

This section specifies what software packages are needed to build and run NAV.
Be aware that many of these packages have dependencies of their own.

Build requirements
------------------

To build NAV, you need at least the following:

 * Python >= 3.9.0
 * Sphinx >= 1.0 (for building this documentation)

Additionally to build frontend assets (like CSS and JS), you will need:

 * Node.js >= 14.0
 * npm >= 6.0

Runtime requirements
--------------------

To run NAV, these software packages are required:

 * Apache2 + mod_wsgi (or, really, any web server that supports the WSGI interface)
 * PostgreSQL >= 13 (With the ``hstore`` extension available)
 * :xref:`Graphite`
 * Python >= 3.9.0
 * nbtscan = 1.5.1
 * dhcping (only needed if using DHCP service monitor)

PostgreSQL and Graphite are services that do not necessarily need to run on
the same server as NAV.

While the required Python modules can be installed from your OS package
manager, most distributions do not provide all of them, or cannot provide them
in the required versions.  We recommend creating a Python virtual environment
(virtualenv), which will ensure NAV's Python requirements do not interfere with
your system Python libraries. Use pip_ to install all Python requirements
from the Python Package Index (PyPI_), using the method described below. The
packages can also be installed from PyPI_ in a separate step, using the pip_
tool and the provided requirements and constraints files::

  pip install -r requirements.txt -c constraints.txt

*However*, some of the required modules are C extensions that will require the
presence of some C libraries to be correctly built (unless PyPI provides binary
wheels for your platform). These include the ``psycopg2`` driver and the
``python-ldap`` and ``Pillow`` modules.

The current Python requirements are as follows:

.. literalinclude:: ../../requirements/django42.txt
   :language: text

.. literalinclude:: ../../requirements/base.txt
   :language: text

.. _pip: https://pip.pypa.io/en/stable/
.. _PyPi: https://pypi.org/

Recommended add-ons
-------------------

If you want to connect a mobile phone to your NAV server and enable SMS alerts
in alert profiles, you will need to install :program:`Gammu` and the Python
:mod:`gammu` module.  The SMS daemon can use plugins to dispatch text
messages through other means, but using Gammu as an SMS dispatcher is the
default.


Installing NAV
==============

First you need to build the static assets. To do this, you will need to have
Node.js and npm installed. Once you have these installed, you can run
the following command to build the CSS assets::

  npm install
  npm run build:sass

This will build the CSS assets and place them in the :file:`python/nav/web/static/css`
directory.

We recommend installing NAV into a Python virtual environment, to avoid
interfering with your system-wide Python libraries.  Pick a suitable path for
the virtual environment (e.g. :file:`/opt/nav`), create it and activate it in
your shell before installing NAV::

  python3 -m venv /opt/nav
  source /opt/nav/bin/activate

To build and install NAV and all its Python dependencies in the activated
virtual environment, run::

  pip install -r requirements.txt -c constraints.txt .

If you want to make sure you can run all NAV programs without first explicitly
activating the virtual environment in a shell, you can add the virtual
environment's :file:`bin` directory to your system's :envvar:`PATH` variable,
e.g.::

  export PATH=$PATH:/opt/nav/bin


.. _initializing-the-configuration-files:

Initializing the configuration
------------------------------

NAV will look for its configuration files in various locations on your file
system. These locations can be listed by running::

  nav config path

.. tip::

   You can override the default configuration search path by setting the
   :envvar:`NAV_CONFIG_DIR` environment variable to point to a directory
   containing your NAV configuration files. When set, this directory will be
   searched with highest priority, before any of the default locations.

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

In this example, type :code:`yes`, hit :kbd:`Enter`, and ensure your web server's
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

  sphinx-build

The resulting files will typically be placed in :file:`build/sphinx/html/`.

If you want to serve this documentation on your NAV web server, you should copy
the :file:`html` directory to a suitable location and make sure that location is served
as ``/doc`` on the web server.  If using the example Apache configuration
(:file:`apache.conf.example`), there is a define named ``documentation_path``,
which can be set to point to this file system location.
