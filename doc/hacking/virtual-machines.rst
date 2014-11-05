========================
Virtual Machines and NAV
========================

Virtualization technology makes working with NAV development much easier. It
also enables user's to try out NAV quickly, using virtual appliances.

NAV's source code includes tools for using Docker_ containers during
development, and for producing an :abbr:`OVF (Open Virtualization
Format)`-based virtual appliance running NAV (for testing or production
purposes).

Building a Docker image
-----------------------

NAV includes a :file:`Dockerfile` that describes a Debian-based Docker image,
which will run all of NAV directly from the source code tree, within a
container. You can read more about this in :doc:`using-docker`.


Build a virtual appliance
-------------------------

The :file:`tools/virtual-appliance/build-virtual-appliance.sh` script uses
Packer_ in conjunction with Virtualbox_ to produce a Debian Wheezy-based
virtual appliance, using the latest release of NAV available from the NAV APT
repository.


.. _Docker: http://www.docker.com/
.. _Packer: http://www.packer.io/
.. _Virtualbox: https://www.virtualbox.org/
