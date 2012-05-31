===========
 snmptrapd
===========

This file contains instructions on how to use the SNMP Trap Daemon NAV
and how to add trap handlers to it.

What is the snmptrapd?
======================

snmptrapd is a program written in Python, designed to receive traps
sent to the NAV server and handing them off to trap handler plugins,
which will process them.  Anyone with some knowledge of Python should
be able to write a new trap handler plugin.

snmptrapd uses the PySNMP library (via NAV's own ``nav.Snmp`` module),
and is loosely base on this example:
http://pysnmp.sourceforge.net/examples/2.x/snmptrapd.html


Usage
=====

snmptrapd can be started and stopped using the regular `nav start` and
`nav stop` commands.  The `snmptrapd.py` program can also be run in
the foreground on the command line, logging all its activites to the
standard output instead of the log file.

snmptrapd must be started as root, as it will bind to the default SNMP
Trap port (UDP port 162). It will drop privileges to the `navcron`
user as soon as the port is bound.


Logging
=======

snmptrapd, when daemonized, logs to two separate files:

`snmptrapd.log`
  Generic log output fra snmptrapd.

`snmptraps.log` 
  Details on every trap received, including unrecognized/unprocessed
  ones.


Configuration
=============

The configuration file `snmptrapd.conf` is divided into sections.
There is one general section for the daemon itself, and sections
specific to each trap handler plugin.


Trap handlers
=============

When snmptrapd receives a trap, it is stored in generic trap object
and offered to each of the trap handlers (that are configured in
`snmptrapd.conf`) in turn.  Each trap handler can inspect the offered
trap and decide to either process it or discard it.

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
