===============================
Controlling log output from NAV
===============================

Overview
========

All NAV subsystems will produce logs about what's going on at any given time.
By default, all NAV daemons will send all log records to the file system.  Log
files from individual subsystems are created in the directory configured by the
``LOG_DIR`` configuration option in :file:`nav.conf`.

The notable exception to this rule is NAV's web subsystem, which is defined as
a WSGI application.  The WSGI application usually runs inside a web server or a
separate WSGI application container, and will by default print all log lines to
its standard error file descriptor.  It is entirely up to the web/application
server to decide where this output is directed (in a typical Apache setup with
``mod_wsgi``, the logs are sent to Apache's defined error log file for the
specific ``VirtualHost``).

Controlling log levels
======================

NAV employs `Python's standard logging facility
<https://docs.python.org/3/library/logging.html>`_, and utilizes a hierarchy of
log handlers for different parts of the codebase.  Most NAV log handlers will
be named after the Python module that uses it, meaning that the log handler
hierarchy will usually correspond to the Python module hierarchy rooted at
``nav``.

All emitted log records will have one of 5 different log levels: **DEBUG**,
**INFO**, **WARNING**, **ERROR** or **CRITICAL**.  NAV's default logging configuration
will only emit log records of level **INFO** or higher.

For most NAV usage, leaving the level at **INFO** is fine.  If, however, you need
to debug a problem or at least get more details out of a specific NAV
subsystem, the log levels of the log handler hierarchy can be controlled
through the configuration file :file:`logging.conf`, whose defaults look like this:

   .. literalinclude:: ../../python/nav/etc/logging.conf

As you can see, this sets the log level of NAV's top-level logger ``nav`` to
*INFO*.  Since the loggers operate in a hierarchy, this level now also applies
to loggers like ``nav.ipdevpoll`` or ``nav.eventengine.queue`` (unless they
have been configured with their own explicit log levels).

If you wish to enable **DEBUG** level logging, it's usually *not recommended*
to set ``nav = DEBUG`` in the ``[levels]`` section: This will cause all parts
of NAV to log in extreme detail, in all log files.  Rather, if you wish to
specifically have debug logging from :program:`ipdevpoll`, you can set
``nav.ipdevpoll = DEBUG``.  This may be OK if you don't know which part of
:program:`ipdevpoll` you are interested in debugging, but it is still going to
be extremely verbose.  If you only wish to get debug details on which plugins
are selected and run for single jobs, you might want to only set
``nav.ipdevpoll.jobs.jobhandler = DEBUG``.

.. note:: Changes to :file:`logging.conf` will not take immediate effect.
          Running NAV processes must either be restarted or sent a ``SIGHUP``
          signal for the configuration file to be re-read.  For the WSGI web
          application, this usually means reloading or restarting the web or
          application server.


Controlling which files logs are sent to
========================================

The :file:`logging.conf` configuration file also contains a ``[files]``
section, which can be used to set up individual log handlers in NAV's hierarchy
to log to specific files (in addition to wherever the logs are already ending
up).  As the example in the default configuration file implies, this can
e.g. be used to get parts of the web application to log to bespoke files, not
just to the web servers log output.

Enabling the example ``nav.web.portadmin = portadmin.log`` will duplicate all
log output from the PortAdmin web tool into the :file:`portadmin.log` file, in
the directory configured by the :file:`nav.conf` ``LOG_DIR`` option.


Using different logging config for individual programs
======================================================

While all NAV programs will look for :file:`logging.conf` in NAV's default
configuration file directories, you can run individual NAV programs with an
explicit logging configuration file that is separate from the standard one.

A typical usage scenario might be that you want to run a single
:program:`ipdevpoll` job with more debug logging, without having the logging
configuration changes affect the :program:`ipdevpolld` daemon running all your
jobs in the background.  This can be achieved by setting the
:envvar:`NAV_LOGGING_CONF` environment variable to point to a different logging
config file before running :program:`ipdevpolld` from the command line.

.. code-block:: console

  $ cat > /tmp/logging.conf <<EOF
  [levels]
  nav = INFO
  nav.ipdevpoll.plugins.system = DEBUG
  EOF
  $ export NAV_LOGGING_CONF=/tmp/logging.conf
  $ ipdevpolld -J inventory -n example-sw
  2023-08-11 13:41:32,124 [INFO nav.ipdevpoll] --- Starting ipdevpolld inventory ---
  2023-08-11 13:41:35,130 [INFO plugins] Imported 31 plugin classes, 31 classes in plugin registry
  2023-08-11 13:41:35,130 [INFO nav.ipdevpoll] Running single 'inventory' job for example-sw.example.org
  2023-08-11 13:41:35,888 [WARNING nav.mibs.hpicf_powersupply_mib.hpicfpowersupplymib] [inventory example-sw.example.org] Number of power supplies in ENTITY-MIB (1) and POWERSUPPLY-MIB (0) do not match
  2023-08-11 13:41:35,892 [WARNING nav.mibs.hpicf_fan_mib.hpicffanmib] [inventory example-sw.example.org] Number of fans in ENTITY-MIB (2) and FAN-MIB (0) do not match
  2023-08-11 13:41:35,894 [DEBUG plugins.system.system] [inventory example-sw.example.org] sysDescr: 'ProCurve J4900B Switch 2626, revision H.08.98, ROM H.08.02 (/sw/code/build/fish(ts_08_5))'
  2023-08-11 13:41:35,894 [DEBUG plugins.system.system] [inventory example-sw.example.org] Parsed version: H.08.98
  2023-08-11 13:41:35,894 [DEBUG plugins.system.system] [inventory example-sw.example.org] found a pre-existing chassis: Chassis/ENTITY-MIB (CN650SE0GJ)
  $

Rotating logs
=============

NAV does not provide its own log rotation.  If you wish to rotate NAV's log
files using an external tool like :program:`logrotate`, you must remember to
configure it to send a ``SIGUP`` signal to each NAV daemon as its log file is
being rotated, or the daemon will continue to write logs to a rotated/deleted
file.

If installing NAV from the Debian packages provided by Sikt, log rotation
through :program:`logrotate` is already provided for you (but you can change
the rotation rules as you see fit).


Advanced logging configuration
==============================

While a few simple use-cases for logging configuration are supported by
:file:`logging.conf`, much more advanced things can be achieved using the
alternative logging configuration file :file:`logging.yml`.  Doing this on your
own, however, usually requires that you know your way around Python and have
extensive knowledge of how the standard Python logging framework works.

:file:`logging.yml` is read and parsed as a Python dictionary, using
:func:`logging.config.dictConfig()`, right after :file:`logging.conf` is read
and parsed.  This means that :file:`logging.yml` must adhere to the
configuration dictionary schema laid out in the Python docs.

Be aware that by adding configuration to :file:`logging.yml`, you are altering
NAV's default logging configuration at a very low level, and you may also be
altering NAV's default behavior of storing logs in files. A :file:`logging.yml`
that replicates a default NAV setup may look something like this:

.. code-block:: yaml

   version: 1
   loggers:
     nav:
       level: INFO
     root:
       handlers: [console]

   formatters:
     default:
       format: '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'

   handlers:
     console:
       class: logging.StreamHandler
       formatter: default

This replicates a setup that logs only **INFO**-level messages and above from
NAV to ``stderr``, using NAV's default log message format.  Individual NAV
daemons will redirect their ``stderr`` streams to their respective log files as
they fork off background processes, so there is no need to redefine these.

Leaving out the :class:`logging.StreamHandler` will still cause the log files
to be created, but they will be empty (save for any outpout to ``stderr`` that
did not come from the :mod:`logging` library).

.. tip:: As with :file:`logging.conf`, processes can be directed to read a
         bespoke :file:`logging.yml` file, but by setting the
         :envvar:`NAV_LOGGING_YML` environment variable instead.

Example: Directing logs to Falcon LogScale (Humio)
--------------------------------------------------

The following example shows how you can make all NAV programs ship their log
messages to a Falcon LogScale (previously known as Humio) ingestor using
something like the `humiologging <https://pypi.org/project/humiologging/>`_
library.  Instead of shipping the file-based logs to LogScale and having them
parsed there, each log record can be shipped with structured attributes/tags.

To achieve something like this, you need to first install the
:mod:`humiologging` library into your NAV installation's Python environment
(e.g. :code:`pip install humiologging`), and then create a :file:`logging.yml`
similar to this:


.. code-block:: yaml

   version: 1
   loggers:
     nav:
       level: DEBUG
     root:
       handlers: [humio, console]

   formatters:
     default:
       format: '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'

   handlers:
     humio:
       class: humiologging.handlers.HumioJSONHandler
       level: DEBUG
       humio_host: https://your-humio-ingest-addr-here
       ingest_token: SECRET_TOKEN_THINGY
     console:
       class: logging.StreamHandler
       formatter: default


This configuration attaches a :class:`HumioJSONHandler` to the ``root`` logger
and sets the global NAV log level to **DEBUG**.  Unfortunately, as this
configuration manipulates the ``root`` logger, it removes the handler(s) that
NAV has by default installed on it, so if you want NAV to also keep logging to
files in addition to Humio, you need to replicate parts of NAV's default setup,
as mentioned in the previous section.  Add an extra handler named ``console``
that logs to a stream (``stderr`` by default), and specify a format for it.

