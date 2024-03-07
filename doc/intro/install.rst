================
 Installing NAV
================

.. highlight:: sh

There are two main options for installing NAV: Either from source code, or from
a pre-packaged version. Some of these options will require manually installing
and/or configuring 3rd party software that NAV depends on, mainly :xref:`PostgreSQL`
and :xref:`Graphite`.


Installing a pre-packaged version of NAV
========================================

There are mainly two official types of "pre-packaged" NAV versions you can use:

1. A virtual appliance.
2. A Debian package.

Installing NAV as a virtual appliance
-------------------------------------

We provide a virtual appliance in the Open Virtualization Format. `Open
Virtualization Format`_ (OVF) is an open standard for packaging and distributing
virtual appliances or, more generally, software to be run in virtual
machines.

Our virtual appliance is based on Debian GNU/Linux and our published Debian
Package, mentioned below. This appliance can be imported into virtualization
software like e.g. Virtualbox or VMWare.

The appliance is useful for quickly evaluating the NAV software, without the
hassle of installing and maintaining a full OS for the purpose.  The appliance
is, however, *not necessarily* suited for production use without modifications
(such as increasing the storage space and other resources made available to
the VM) or proper sysadmin practices.

`There is a separate guide for installing the virtual appliance on the official
NAV web site <https://nav.uninett.no/install-instructions/#ovf>`_ .

.. _`Open Virtualization Format`: https://en.wikipedia.org/wiki/Open_Virtualization_Format

Installing NAV from a Debian Package
------------------------------------

If you are familiar with the `Debian GNU/Linux operating system
<https://www.debian.org>`_, you can install NAV from a Debian Package. Debian
is our primary choice of server operating system, so we always make sure to
provide an official Debianized NAV package.

Using the Debian package will save you from the hassle of installing and
upgrading either NAV or its dependencies from source code. You can even
configure your Debian to automatically keep up-to-date with the latest security
patches from the Debian team.

This is normally our recommended option for regular NAV users.

`Instructions for installing the Debian package are available on the official
NAV web site <https://nav.uninett.no/install-instructions/#debian>`_.

After installing the Debian package, you will need to :ref:`integrate Graphite
with NAV <integrating-graphite-with-nav>`, before starting to use NAV to
monitor your devices.


Installing NAV using Docker Compose
-----------------------------------

There is also a third, still experimental, way of installing a pre-packaged
NAV: `Docker Compose`_. Like with the Virtual Appliance, this offers a quick
way to get started with NAV, without the up-front hassle of installing and
configuring a full operating system for the purpose.

Using Docker Compose, NAV's components and dependencies will run in individual
ready-to-use containers. You can run NAV directly from your workstation for
evaluation, on a server with other containers, or more easily scale out to
multiple servers, if need be.

The containerized version of NAV is available from a separate GitHub
repository: https://github.com/Uninett/nav-container/

.. _`Docker Compose`: https://docs.docker.com/compose/


Installing NAV from source code
===============================

If you're the hacker type, or just want to run NAV on your own preferred choice
of \*NIX flavored operating system, you'll want to build and install NAV from
source code.

For you, we provide two guides:

1. :doc:`A generic guide to installation from source
   </howto/generic-install-from-source>`.
2. :doc:`A step-by-step, detailed guide on installing NAV from source on a
   Debian GNU/Linux operating system </howto/manual-install-on-debian>`.

