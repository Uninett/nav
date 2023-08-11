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
