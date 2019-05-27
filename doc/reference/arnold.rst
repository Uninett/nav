======
Arnold
======

Introduction
============

Arnold is a port-blocker and vlan changer, and was originally made to be able to
easier remove mischievers from the campus-internet.

This document will give you information about how Arnold works and how to use
and configure it. A FAQ-section will be added as questions are received.

What does Arnold do?
====================

Arnold is a system that blocks or changes vlan on (we use the label *detains*)
switch-ports by using SNMP-set commands. Arnold uses an IP- or MAC-address to
locate the switch-port the address is operating from using the NAV-database, and
then attempts to detain it.

.. note:: You **must** assign a *write-enabled* SNMP profile to your devices,
          otherwise Arnold will not be able to detain or enable ports on
          them. You can select profiles for devices individually in the *Seed
          Database* tool.

Using Arnold
============

Arnold consists of a couple of scripts, configuration files and a
web-interface. For basic use you will use the web-interface to disable and
enable ports. Automatic use of Arnold requires some setup and use of cron to
execute jobs periodically.

The web-interface
-----------------

The web-interface is accessible from the Toolbox. When using Arnold you have
several views available. They are as follows:

- **History** lists the detentions for the last x days. This will list both
  active detentions and detentions no longer in effect.
- **Detained ports** lists all active detentions.
- **Detention reasons** lists all existing reasons for a detention. A reason is
  directly connected to a detention, and makes it easy to group detentions by
  reasons.
- **Quarantine vlans** lists all existing quarantine vlans. Instead of shutting
  down the port, you can switch the access vlan to that of a quarantine
  vlan. This vlan could be configured for instance to rate limit traffic or be
  restricted in some other way.
- **Detention profiles** lists all detention profiles. A detention profile is
  used when executing automatic detentions.

In addition you have two actions you can use - *Search* and *Manual detention*.

- **Search** lets you search for detentions given some search parameters.
- **Manual detention** lets you manually detain a port given an IP- or 
  MAC-address.

Predefined detentions
---------------------
The only way to use a predefined detention is by using the ``start_arnold.py``
shell script. After creating a predefined detention you usually want to create a
cron-job for running the script with some input parameters. See section about
`start_arnold.py`_.


Using the scripts
=================

Arnold consists of three scripts, which all are located in the ``nav/bin``
directory.

- **autoenable.py** enables ports based on the autoenable variable available for
  both manual and predefined detentions.
- **start_arnold.py** is used in combination with predefined detentions to
  invoke a series of detentions.
- **t1000.py** verifies that the MAC-addresses that should be offline are not
  active on other ports. If a detained MAC-address is online on another port, it
  will try to detain it there aswell.

More details about the different scripts can be seen below.

autoenable.py
-------------

*autoenable.py* fetches all detained ports with an autoenable-value and enables
each of those detentions if the time is due. It can be run manually or as a
periodic cron job.

The simplest way of running automatic enabling periodically is to create a file
containing cron configuration that calls the *autoenable.py* program as often as
you would like::

  0 * * * * some_prefix/nav/bin/autoenable.py  # Run every hour on the hour

Save this snippet in a file called ``autoenable`` in NAV's ``etc/cron.d/``
directory. That way, you can add it to the navcron user's crontab by calling
``nav start autoenable``.

start_arnold.py
---------------

When a predefined detention is created you can use *start_arnold.py* to invoke a
series of detentions based on the input to the script.

If the file or list of addresses exist locally then you can pipe it in using for
instance ``cat``::
  
  # cat scanresult.txt | nav/bin/start_arnold_py -i

or you can do it from a remote server using ssh commands::

  # cat scanresult.txt | ssh scanner@navinstall.network.com:nav/bin/start_arnold_py -i
  
To avoid having to type passwords you want to create public keys, like described
for instance `here <http://www.linuxproblem.org/art_9.html>`_.

File format
~~~~~~~~~~~

Each line in this file is assumed to consist of an IP- or MAC-address and
optionally a comment (separated by a space). For each valid address a detention
will be made. Lines starting with *#* will be skipped.

t1000.py
--------

This script needs to be set up to run in the same way as `autoenable.py`_.

*t1000.py* fetches all detained ports and checks if the MAC-address which was
behind the detained port is active on another port. If it is, it enforces the
detention on that port aswell. Depending on options given at detention-time it
will either remove the detention on the old port or just leave it.

.. warning:: This does not detain the new port immediately after a detained
   computer has moved to it, because it takes some time before NAV discovers the
   new location of the MAC-address. This combined with the interval t1000.py
   runs in could give the user quite some time with access before being detained
   again. This on-and-off behavior of internet access has been known to cause
   confusion and annoyance among the users - use this script knowing that.

Configuring Arnold
==================

Config files
------------

The following configuration files are used by Arnold.

arnold.conf
~~~~~~~~~~~

``nav/etc/arnold/arnold.conf`` is divided into three sections.

- **arnold** is the section that contains information about what database to use
  and on what networking equipment Arnold should be able to detain ports. You
  also define email-addresses here.
- **loglevel** is deprecated. See the section about `Logging`_.
- **arnoldweb** has just one config option, which sets the default detention
  method when loading the web interface.

nonblock.conf
~~~~~~~~~~~~~

``nav/etc/arnold/nonblock.conf`` is not really a config-file but an exception
list. Some addresses should, for various reasons, not be detained. They can be
added to this file. The format is defined in the file, and supports single
addresses, lists and subnets.

On reading this file you will maybe notice options for defining netbox types
that are to be ignored. This is a deprecated option that existed because Arnold
had trouble communicating with some types of equipment. These kind of problems
are now handled automatically.

Mailtemplates
~~~~~~~~~~~~~

``nav/etc/arnold/mailtemplates/*``

When creating a predefined detention there is an option for “Path to mailfile”.

Arnold is able to send mail to those listed as responsible for the address it
tries to detain. The mail-address is the contact address defined for an
organisation derived for this IP- or MAC-address. You have to create the mail
template yourself. The default template directory contains a README-file that
has more information about how to create a template.

Logging
=======

The arnold scripts logs to individual files stored in
``nav/var/log/arnold/``. The webinterface logs to STDERR, which Apache most
probably puts in it's error.log. The loglevel used for each script must be set
in ``logging.conf``.

The loggers (with default loglevels) are::

  start_arnold = INFO
  t1000 = INFO
  autoenable = INFO


FAQ
===

Missing interfaces
------------------

When an interface that is a part of a detention is removed from NAV, commonly
by removing the switch, Arnold will display a message regarding this. The
last known interface and switch will be displayed.

To close this detention just enable it manually. **This will not send any
commands to any network equipment**, only close the detention as seen from
the web interface.
