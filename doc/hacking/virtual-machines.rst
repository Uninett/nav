========================
Virtual Machines and NAV
========================

Virtualization technology makes working with NAV development much easier. It
also enables user's to try out NAV quickly, using virtual appliances.

NAV's source code includes tools for using Docker_ containers during
development, and for producing an :abbr:`OVF (Open Virtualization
Format)`-based virtual appliance running NAV.

Building a Docker image
-----------------------

The :file:`Dockerfile` describes a Debian-based Docker image including all
dependencies needed to to build and run NAV on a single system.

The generated image will expect your NAV source code directory to be mounted
in the container at :file:`/source` . For your own convenience, you should
also port forward the container ports 22, 80 and 8000 to have access to the
SSH server, the NAV web interface and the Graphite web interface respectively.


Build a virtual appliance
-------------------------

The :file:`tools/virtual-appliance/build-virtual-appliance.sh` script uses
Packer_ in conjunction with Virtualbox_ to produce a Debian Wheezy-based
virtual appliance, using the latest release of NAV available from the NAV APT
repository.


.. _Docker: http://www.docker.com/
.. _Packer: http://www.packer.io/
.. _Virtualbox: https://www.virtualbox.org/
