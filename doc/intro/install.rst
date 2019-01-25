================
 Installing NAV
================

.. highlight:: sh

NAV releases official debian packages. We recommend using these if you can. If
you cannot, read on.

Install from source on Debian 9
===============================

See :doc:`/howto/manual-install-on-debian`.


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
