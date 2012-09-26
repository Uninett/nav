=========
ipdevpoll
=========

ipdevpoll is the main SNMP collection engine of NAV. Its work is divided into
jobs, which runs a series of collection plugins for each IP device at set
intervals. These jobs are fully user-configurable.

Usage
=====

::

  Usage: ipdevpolld [options]

  Options:
    --version             show program's version number and exit
    -h, --help            show this help message and exit
    -f, --foreground      run in foreground instead of daemonizing
    -s, --log-stderr      log to stderr instead of log file
    -j, --list-jobs       print a list of configured jobs and exit
    -p, --list-plugins    load and print a list of configured plugins
    -J JOBNAME            run only JOBNAME in this process
    -n NETBOX, --netbox=NETBOX
			  Run JOBNAME once for NETBOX. Also implies -f and -s
			  options.
    -m, --multiprocess    Run ipdevpoll in a multiprocess setup
    -P, --pidlog          Include process ID in every log line

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

ipdevpoll is configured in ``ipdevpoll.conf``. This is an `ini`-style
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

  How many values to ask for in each SNMP `GETBULK` request, 50 being the
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
  run at any given time. The default is ``0``, meaning *unlimited*.

