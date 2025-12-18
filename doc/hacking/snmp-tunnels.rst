=========================================
Establishing SNMP tunnels using socat/SSH
=========================================

While developing new functionality related to SNMP collection in NAV,
a developer's workstation isn't necessarily attached to a network that
provides the developer with the necessary access to communicate with the
required set of switches/routers etc. For internal equipment, this is
usually solved by connecting via VPN, but sometimes, the devices one needs
to talk to is located at a customer site where there is no VPN access.

In the case of having SSH access to a Linux server at the customer premises,
that is allowed to communicate with the customer's switches and routers,
one can establish an SNMP tunnel to the customer's equipment using a
combination of SSH and socat.

This guide will document two ways to establish such an SNMP tunnel: one using
docker and one without.

Course of action - with docker
==============================

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
=============================
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

Course of action - without docker
=================================

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
================================

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
