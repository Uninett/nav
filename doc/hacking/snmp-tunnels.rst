=========================================
Tunneling SNMP traffic during development
=========================================

While developing new functionality related to SNMP collection in NAV, a
developer's workstation isn't necessarily attached to a network that lets it
talk to the switches and routers it needs. For internal equipment, this is
usually solved by connecting via VPN, but sometimes the devices one needs to
talk to are located at a customer site without VPN access.

If you have SSH access to a server that *is* allowed to talk SNMP to those
devices (typically the customer's NAV server), you can tunnel your SNMP traffic
through it. This guide describes two ways to do that:

* :ref:`sshuttle <snmp-tunnels-sshuttle>`, the recommended method on Linux. It
  tunnels traffic to any number of devices at once, using their real IP
  addresses (both IPv4 and IPv6). This means a database snapshot copied from
  the customer's NAV installation works as-is: ipdevpoll, ``navsnmp`` and the
  net-snmp command line tools all talk to the devices just as they would on
  the customer's server.

* :ref:`SSH and socat <snmp-tunnels-socat>`, which works on any operating
  system, but tunnels only one device per tunnel, and requires you to address
  the device by a local address or a made-up host name.


.. _snmp-tunnels-sshuttle:

Using sshuttle (Linux)
======================

What is sshuttle?
-----------------

`sshuttle <https://sshuttle.readthedocs.io/en/stable/>`_ is a "poor man's VPN"
built on top of SSH. You give it an SSH destination and a list of subnets.
sshuttle then intercepts all traffic from your machine to those subnets, and
relays it through the SSH connection. On the remote end, the traffic is sent
on from the SSH server, as if it originated there.

sshuttle needs no root access, and no software except Python, on the remote
server. On your own machine, it needs root to set up the firewall rules that
intercept the traffic. You don't need prior experience with sshuttle to follow
this guide, but its `usage documentation
<https://sshuttle.readthedocs.io/en/stable/usage.html>`_ is a good read if
you want to know more.

NAV's SNMP traffic is UDP, which sshuttle can only tunnel using its *tproxy*
method (the default *nat* method only handles TCP over IPv4). The tproxy
method has a few extra requirements, described in `sshuttle's TPROXY
documentation <https://sshuttle.readthedocs.io/en/stable/tproxy.html>`_. The
helper script described below takes care of these for you.

Requirements
------------

On your own machine:

* Linux. The tproxy method relies on Linux-specific kernel features.
* sshuttle (see `sshuttle's installation instructions
  <https://sshuttle.readthedocs.io/en/stable/installation.html>`_; most Linux
  distributions package it).
* The ``ip`` command (usually from the *iproute2* package), and *both* the
  ``iptables`` and ``ip6tables`` commands. sshuttle refuses to use the tproxy
  method unless both are present.
* ``sudo`` access.

On the remote server:

* An account you can log in to using SSH. Logging in with a password works
  fine; see :ref:`snmp-tunnels-ssh-keys` if you'd rather use an SSH key, or
  if the server requires one.
* Python 3.10 or newer (see `sshuttle's requirements
  <https://sshuttle.readthedocs.io/en/stable/requirements.html>`_).
* Permission to talk SNMP to the devices. On a customer's NAV server this is
  normally a given, since NAV polls the devices from there. Network equipment
  often restricts SNMP access to specific source addresses, and the SNMP
  traffic will arrive from the server's address, not yours.

Opening the tunnel
------------------

NAV ships two helper scripts in :file:`tools/`:

:file:`tools/sshuttle-tunnel.sh`
  Opens the tunnel. It checks the requirements, sets up the policy routing
  that the tproxy method needs, runs sshuttle, and removes the routing again
  when you close the tunnel.

:file:`tools/sshuttle-subnets.py`
  Looks up the management IP addresses of the IP devices in your local NAV
  database, and reduces them to a reasonable list of subnets to route through
  the tunnel.

In the most common case, you have restored a copy of the customer's NAV
database into your development environment, and want to reach all the devices
in it. With your NAV development environment active (so that
:file:`tools/sshuttle-subnets.py` can read the database), run:

.. code-block:: sh

   tools/sshuttle-tunnel.sh user@remote-server

The argument is the SSH destination of the remote server, in any form that
``ssh`` accepts, including host aliases from your :file:`~/.ssh/config`. The
script prints the subnets it is about to route, explains what it needs sudo
for, and then asks for your sudo password. Unless you are using an SSH key
(see below), ``ssh`` will then ask for your password on the remote server,
just like it normally would. The tunnel stays open until you press
:kbd:`Ctrl-C`.

To route something else than the default selection, list the subnets or
addresses explicitly after the SSH destination:

.. code-block:: sh

   tools/sshuttle-tunnel.sh user@remote-server 192.0.2.0/24 2001:db8:1::/64 198.51.100.7

or use :file:`tools/sshuttle-subnets.py` to select a subset of IP devices. It
accepts the same filter expressions as the ``navdf`` command:

.. code-block:: sh

   tools/sshuttle-tunnel.sh user@remote-server \
     $(tools/sshuttle-subnets.py "filter(type__vendor__id='juniper')")

By default, :file:`tools/sshuttle-subnets.py` groups the IP addresses into
``/24`` (IPv4) and ``/64`` (IPv6) subnets, and routes a whole subnet when at
least two of the addresses fall within it. Lone addresses are routed
individually. Run it with ``--help`` to see how to adjust this, or use
``--host-routes`` to route only the exact addresses of the selected IP
devices. Add ``-v`` to see how many devices each subnet covers.

.. warning::

   Every connection your machine makes to the routed subnets will go through
   the tunnel while it is open, not just SNMP traffic from NAV. Keep the list
   of subnets as narrow as is practical.

.. _snmp-tunnels-ssh-keys:

Using your SSH key
~~~~~~~~~~~~~~~~~~

If you normally log in to the remote server using an SSH key, or the server
doesn't accept passwords at all, the tunnel can use your key too. There is one
catch: since ``ssh`` runs as root (see below), it can only use your key through
your *SSH agent*, the background program that holds your unlocked keys in
memory. Key files in your own :file:`~/.ssh` directory are not picked up on
their own.

So, before starting the tunnel:

1. Make sure your key is loaded into your agent. ``ssh-add -l`` lists the
   loaded keys, and ``ssh-add`` (optionally followed by the path to a key file)
   loads one. See `ssh-add(1) <https://man.openbsd.org/ssh-add>`_ and
   `ssh-agent(1) <https://man.openbsd.org/ssh-agent>`_ for details.

2. Make sure the ``SSH_AUTH_SOCK`` environment variable is set in the shell
   you start the script from. Most desktop environments set this up for you.
   The script tells you whether it found an agent, and hands it over to
   ``ssh``.

If you don't have a key yet, but want one, `ssh-keygen(1)
<https://man.openbsd.org/ssh-keygen>`_ creates it, and ``ssh-copy-id
user@remote-server`` installs it on the server.

Why does it need sudo?
~~~~~~~~~~~~~~~~~~~~~~

:file:`tools/sshuttle-tunnel.sh` uses sudo for two things, and prints every
command it runs as root:

1. Adding *policy routing* rules (routing table 100, firewall mark ``0x1``) for
   both IPv4 and IPv6. sshuttle's tproxy method marks the packets it wants to
   intercept, and these rules make sure the marked packets are delivered to
   sshuttle on your own machine. The rules are given a high priority, so that
   they also work when you're connected to a VPN that routes all your traffic.
   Rules that are already present are left alone, and the rules the script
   added are removed when it exits.

2. Running sshuttle itself as root, since its tproxy method needs root
   privileges to set up firewall rules and transparent proxy sockets.

Because sshuttle then starts ``ssh`` as root, the script hands your SSH agent,
your :file:`~/.ssh/config` and your :file:`~/.ssh/known_hosts` file over to
it. It also asks ``ssh`` which user name your configuration would log in with,
and passes it on explicitly, since ``ssh`` running as root would otherwise log
in as ``root``. Host aliases and other settings in your SSH configuration keep
working, with one exception: a ``~`` in your configuration file now refers to
root's home directory.

sshuttle would also intercept its own SSH connection if the remote server's
address is within one of the routed subnets, which breaks the tunnel. The
script therefore tells sshuttle to exclude the server's SSH port.

Testing the tunnel
------------------

With the tunnel open, test it using ``navsnmp`` and any of the net-snmp tools.
``navsnmp`` prints the SNMP command line options (including credentials) that
NAV has stored for an IP device, so you don't need to type them:

.. code-block:: sh

   snmpwalk $(navsnmp my-switch.example.org) SNMPv2-MIB::system

You can also use the *check connectivity* button when editing the IP device in
SeedDB, or run ipdevpoll against the device:

.. code-block:: sh

   ipdevpolld -J inventory -n my-switch.example.org

When NAV runs inside containers
-------------------------------

.. TODO: This section is unverified. sshuttle documents that it only
   intercepts traffic from the local machine unless it listens on a
   non-loopback address (``--listen 0.0.0.0:0``). Traffic from a
   devcontainer or the legacy docker compose setup is forwarded by the host,
   so it probably needs that option, which tools/sshuttle-tunnel.sh cannot
   pass on yet. Verify before publishing.

If you run NAV directly on your machine, for instance with the
:ref:`minimal docker setup <minimalist-docker-dev>` (where only PostgreSQL and
Graphite run in containers), everything above applies as-is.

If NAV itself runs inside a container (as with devcontainers or the legacy
docker compose setup), its SNMP traffic reaches the tunnel by being forwarded
through your machine, rather than originating on it. sshuttle only
intercepts forwarded traffic when it listens on a non-loopback address; see
the ``--listen`` option in `sshuttle's usage documentation
<https://sshuttle.readthedocs.io/en/stable/usage.html>`_.

Troubleshooting
---------------

*The script complains about missing tools, or refuses to run*
  It checks for everything it needs before doing anything, and explains why
  each missing tool is needed. Install the missing packages and try again.

*ssh asks for a password, although you meant to use your SSH key*
  See :ref:`snmp-tunnels-ssh-keys`: the key must be loaded into your SSH
  agent, and ``SSH_AUTH_SOCK`` must be set. Also, if your `SSH configuration
  <https://man.openbsd.org/ssh_config>`_ combines ``IdentitiesOnly yes`` with
  an ``IdentityFile ~/...`` setting, the ``~`` now points to root's home
  directory, and ssh may refuse to use the key from your agent.

*sudo refuses to preserve the environment*
  The script runs sshuttle using ``sudo --preserve-env=SSH_AUTH_SOCK``. This
  requires that your sudo configuration lets you set environment variables
  (the ``SETENV`` tag, which is implied when you are allowed to run all
  commands).

*The tunnel is up, but devices don't answer SNMP requests*
  Check that the remote server itself can talk to the device (e.g. run
  ``snmpwalk`` on the remote server), and that the address you are using is
  actually among the routed subnets printed by the script.

*Routing rules are left behind after a crash*
  If the script is killed without getting the chance to clean up, its policy
  routing rules remain. List them using ``ip rule show fwmark 0x1`` and
  ``ip -6 rule show fwmark 0x1``. Remove them like this:

  .. code-block:: sh

     sudo ip rule del pref 1 fwmark 0x1 lookup 100
     sudo ip -6 rule del pref 1 fwmark 0x1 lookup 100
     sudo ip route del local default dev lo table 100
     sudo ip -6 route del local default dev lo table 100


.. _snmp-tunnels-socat:

Using SSH and socat (any operating system)
==========================================

This method combines an SSH port forward with ``socat``, which converts
between UDP (which SNMP uses) and TCP (which SSH can forward). Each tunnel
reaches exactly one device. The remote server needs ``socat`` installed.

With docker
-----------

1. Replace the build arguments ``USER`` and ``UID`` in
   :file:`docker-compose.snmp.yml` with your own username and user ID (the
   latter is mostly important on Linux, as this ensures bind-mounted files are
   readable with *your* permissions.  Also, replace the runtime ``user``
   argument with your username.

2. Copy the contents of :file:`docker-compose.snmp.yml` into
   :file:`docker-compose.override.yml` (or explicitly specify this file to
   ``docker compose up`` later, like this: ``docker compose -f
   docker-compose.yml -f docker-compose.snmp.yml up``).

3. Change the line ``command: 192.168.0.1 user@my-hop-host 10000`` to the ip
   address or name of the device you want to reach, the relevant hop host and
   whatever port you want to tunnel through.  This port should be free to use
   on the hop-host.

4. Make sure that ssh key to the hop host is saved (you can test this by doing
   ``ssh user@my-hop-host``, it is saved if you're not prompted for a password).
   If you haven't generated an SSH key yet you can run `ssh-keygen` and follow
   the prompts. Afterwards you can use
   ``ssh-copy-id -i ~/.ssh/mykey user@my-hop-host`` to copy that key to the
   server.

5. Now you can start nav.

6. In SeedDB: Add an SNMP management profile with the community for the device.

7. In SeedDB: Add an IP device with the IP "mydevice.mydomain" and the
   management profile created in step 6. Click on "check connectivity", which should
   be answering "ok".

Troubleshooting - with docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When starting docker:

- the error message
  ``mydevice.mydomain_1  | bind [::1]:10000: Cannot assign requested address``
  can be ignored, it should still work

- if the error message
  ``mydevice.mydomain_1  | 2023/02/21 13:36:11 socat[1744] E bind(5,
  {AF=2 0.0.0.0:10000}, 16): Address already in use``
  appears: change the port in the docker file. Some other process on the hop-host is
  using this port.

When adding IP device in SeedDB:

- if an error message appears go into the docker container using
  ``docker compose exec nav /bin/bash`` and do ``ping mydevice.mydomain``. If that
  works, then make sure you're using the right management profile, because
  tunneling works.

Without docker
--------------

1. Forward a TCP port from your machine to another, which has the necessary
   SNMP access level.

   .. code-block:: sh

      ssh -L 1161:localhost:1161 user@the-machine-with-access

2. Then, on that port, set up a UDP-to-TCP tunnel using socat on that machine:

   .. code-block:: sh

      socat tcp4-listen:1161,reuseaddr,fork UDP:ip-or-name-of-switch-to-talk-to:161

3. In a different terminal window, on your localhost, set up a socat
   tunnel to tunnel UDP traffic on port 161 through the forwarded TCP port
   (sudo is necessary because you need to bind to port 161, which only root can do):

   .. code-block:: sh

      sudo socat -T15 udp4-recvfrom:161,reuseaddr,fork tcp:localhost:1161

4. Finally, to test connectivity in another terminal window:

   .. code-block:: sh

      snmpwalk -v2c -c public localhost SNMPv2-MIB::system

   (replace ``public`` with the respective community string if it differs)

5. When tunneling works you can add a new management profile with the
   respective community string the switch uses to NAV.

6. Then add an IP device with that management profile and 127.0.0.1 as
   IP address.

Troubleshooting - without docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- if in step 2 the error "Address already in use" appears, you can figure
  out which process is using it by running

  .. code-block:: sh

      sudo netstat -aupn

  (these flags are Linux specific, use

  .. code-block:: sh

      man netstat

  to figure out which flags might be helpful on other operating systems).

  Then kill the process by running

  .. code-block:: sh

      sudo kill process_id

  If the process restarts on its own it might be that you need to kill its
  parent process. This command can help identify the parent process:

  .. code-block:: sh

      ps axuwf
