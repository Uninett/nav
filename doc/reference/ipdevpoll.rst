=========
ipdevpoll
=========

ipdevpoll is the main SNMP collection engine of NAV. Its work is divided into
jobs, which runs a series of collection plugins for each IP device at set
intervals. These jobs are fully user-configurable.

Usage
=====

::

    usage: ipdevpolld [-h] [--version] [-f] [-s] [-j] [-p] [-J JOBNAME]
		      [-n NETBOX] [-m [WORKERS]] [-M JOBS] [-P] [--capture-vars]
		      [-c] [--threadpoolsize COUNT] [--worker]

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      -f, --foreground      run in foreground instead of daemonizing
      -s, --log-stderr      log to stderr instead of log file
      -j, --list-jobs       print a list of configured jobs and exit
      -p, --list-plugins    load and print a list of configured plugins
      -J JOBNAME            run only JOBNAME jobs in this process
      -n NETBOX, --netbox NETBOX
			    Run JOBNAME once for NETBOX. Also implies -f and -s
			    options.
      -m [WORKERS], --multiprocess [WORKERS]
			    Run ipdevpoll in a multiprocess setup. If WORKERS is
			    not set it will default to number of cpus in the
			    system
      -M JOBS, --max-jobs-per-worker JOBS
			    Restart worker processes after completing JOBS jobs.
			    (Default: Don't restart)
      -P, --pidlog          Include process ID in every log line
      --capture-vars        Capture and print locals and globals in tracebacks
			    when debug logging
      -c, --clean           cleans/purges old job log entries from the database
			    and then exits
      --threadpoolsize COUNT
			    the number of database worker threads, and thus db
			    connections, to use in this process
      --worker              Used internally when lauching worker processes

    This program runs SNMP polling jobs for IP devices monitored by NAV

Manually running a job for a given netbox
-----------------------------------------

Unscheduled runs of jobs can be run against any NAV-monitored device from the
command line. To run the ``inventory`` job for the switch
``some-sw.example.org``, type::

  ipdevpolld -J inventory -n some-sw

The ``-n`` argument can be given as a prefix of a device's sysname, or as an
IP address (the device still needs to be registered in NAV).


Configuring ipdevpoll
=====================

ipdevpoll is configured in :file:`ipdevpoll.conf`. This is an "ini"-style
configuration file with multiple sections.

Section [ipdevpoll]
-------------------

``logfile``
  Where to put log messages.  If this starts with ``/`` or ``.`` it will be
  interpreted literally.  Otherwise, the file will be created in the NAV log
  directory.

``max_concurrent_jobs``
  The maximum number of concurrent jobs within a single ipdevpoll process. It
  may be necessary to adjust this if you keep running out of available file
  descriptors

Section [snmp]
--------------

This section is used to change the SNMP polling parameters from their
defaults.

``timeout``
  The initial timeout value for a request, given as a number of seconds. All
  requests will be retried up to three times, with an exponential increase in
  the timeout value. The default is *1.5* seconds.

``max-repetitions``
  How many values to ask for in each SNMP `GETBULK` request, 10 being the
  default.


Section [plugins]
-----------------

Used to list all the plugins to load into an ipdevpoll process, and assign
them short aliases.  Plugins are loaded from the built-in
:py:mod:`nav.ipdevpoll.plugins` package unless a fully qualified class name is
supplied as a value.  To load your homebrew plugin class :py:class:`Foo` from
the :py:mod:`homebrew.foo` module, add::

  foo = homebrew.foo.Foo

To load the built-in :py:mod:`snmpcheck` plugin from the
:py:mod:`nav.ipdevpoll.plugins` package, all that is needed is::

  snmpcheck=

Section [prefix]
----------------

``ignored``
  A list of IPv4 and/or IPv6 prefixes that should never be inserted into the
  database, even if they are collected from a device's interfaces.


Section [linkstate]
-------------------

``filter``
  Selects a filter for generating ``linkState`` alerts when link state changes
  are detected on interfaces. The default value is ``topology``, indicating
  that alerts should only be generated for interfaces that have been detected
  as an uplink or downlink.

  The value ``any`` will generate alerts for all link state changes, but
  **this is not recommended** for performance reasons.

Job sections
------------

Any section whose name starts with the ``job_`` prefix defines a new job
configuration. The following settings can be configured for jobs:

``interval``
  How often the job should be scheduled for each device. Values can be given a
  unit suffix of ``s``, ``m`` or ``h`` to indicate seconds, minutes or hours.

``plugins``
  A sequence of plugins to run in this job. Given as a space-separated list of
  names as configured in the global ``[plugins]`` section.

``intensity``
  An internal per-process limit on how many concurrent jobs of this type can
  run at any given time.


.. _ipdevpoll-multiprocess:

Multiprocess mode
=================

ipdevpoll runs all polling tasks asynchronously in a single thread. Threads
are reserved for synchronous communication with the PostgreSQL database
backend. Even on a multi-core server, this means all of ipdevpoll's work is
limited to a single core. Once ipdevpoll's workload grows beyond what a single
core can handle, ipdevpoll can optionally run in a *multiprocess mode*, using
the :option:`--multiprocess` option.

In multiprocess mode, ipdevpoll spawns a number of worker processes, while the
master process becomes a simple job scheduler, distributing the actual jobs to
the individual workers.

.. warning::

   ipdevpoll's default number of workers processes and threads aren't
   necessarily sane for multiprocess usage. Unless a number of workers is
   supplied to the :option:`--multiprocess` option, it will spawn a number of
   workers corresponding to the number of cores it detects on your system. The
   default number of database threads in ipdevpoll's threadpool is **10** per process,
   which means each worker process will create **10 individual connections to
   PostgreSQL**.

   These numbers multiply fast, and can end up easily saturating PostgreSQL's
   default pool of 100 available connections, causing other NAV processes to
   be unable to connect to the database. When enabling multiprocess mode, you
   should really tune down the threadpool size by adding the
   :option:`--threadpoolsize` option.


Another good thing about the multiprocess mode is that you can limit the
number of jobs any worker process will run before it is killed and respawned.
This may provide additional protection against unintended resource leaks. See
the :option:`--max-jobs-per-worker` option.

You can make sure ipdevpoll always runs in multiprocess mode by altering the
``command`` option in the ``ipdevpoll`` entry of the configuration file
:file:`daemons.yml`.
