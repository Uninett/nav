===========
 snmptrapd
===========

What is the SNMP trap daemon?
=============================

:program:`snmptrapd` (a.k.a. :program:`navtrapd` to avoid name conflicts with
Net-SNMP's similarly named trap daemon) is a NAV backend service program,
designed to receive SNMP trap messages sent to the NAV server. It hands trap
messages off to trap handler plugins, which will process them, and typically
translate them into NAV events as they see fit.  Anyone with some knowledge of
Python and SNMP should be able to write a new trap handler plugin.

snmptrapd uses the :mod:`pynetsnmp-2` library (via NAV's own :py:mod:`nav.Snmp`
adapter module), but is loosely based on this example from the PySNMP library:
http://pysnmp.sourceforge.net/examples/2.x/snmptrapd.html


Usage
=====

snmptrapd can be started and stopped using the regular `nav start` and
`nav stop` commands.  The :program:`snmptrapd` program can also be run in
the foreground on the command line, logging all its activites to the
standard output instead of the log file.

snmptrapd must be started as root, as it will bind to the default SNMP trap
port (UDP port 162). It will drop privileges to the ``navcron`` user as soon as
the port is bound.

::

    usage: navtrapd [-h] [-d] [-c COMMUNITY] [address [address ...]]

    NAV SNMP Trap daemon

    positional arguments:
      address

    optional arguments:
      -h, --help            show this help message and exit
      -d, --daemon          Run as daemon
      -c COMMUNITY, --community COMMUNITY
			    Which SNMP community incoming traps must use. The
			    default is 'public'

    One or more address specifications can be given to tell the trap daemon which
    interface/port combinations it should listen to. The default is 0.0.0.0:162,
    and, if the system appears to support IPv6, also [::]:162, which means the
    daemon will accept traps on any IPv4/IPv6 interface, UDP port 162.


Logging
=======

snmptrapd, when daemonized, logs to :file:`snmptrapd.log`.

When developing new handler modules, or otherwise debugging trap reception in
NAV, it may be desirable to log full dumps of the trap packet contents. This
can be done by setting the loglevel ``nav.snmptrapd.traplog = DEBUG`` in NAV's
logging configuration (:file:`logging.conf`).

.. note:: ``nav.snmptrapd.traplog`` will log the full contents of any received
          trap, whether any handler modules decided to act on the trap or not.

Configuration
=============

The configuration file `snmptrapd.conf` is divided into sections.
There is one general section for the daemon itself, and sections
specific to each trap handler plugin.


Trap handlers
=============

When snmptrapd receives a trap, it is stored in generic trap object
(:class:`nav.snmptrapd.trap.SNMPTrap`).

and offered to each of the trap handlers (that are configured in
`snmptrapd.conf`) in turn.  Each trap handler can inspect the offered trap and
decide to either process it or discard it.

A trap handler plugin is a Python module that must provide a function
called ``handleTrap()``.

.. function:: handleTrap(trap, config)

   Takes a trap object and a ConfigParser reference.  Processes or
   discards the trap and returns a status value.

There is template module for a handler plugins, called
`handlertemplate.py`.  It contains some comments and shows the basics
you need to write your own trap handler.

.. NOTE::
   For a trap handler to take effect, snmptrapd must first be restarted.


nav.snmptrapd.trap.SNMPTrap
---------------------------

.. warning:: This class interface is subject to change in the future, as the
             member naming is not according to our :pep:`8`-based naming
             standard (``camelCase`` vs. ``under_score``)


.. autoclass:: nav.snmptrapd.trap.SNMPTrap
   :members:
   :show-inheritance:
