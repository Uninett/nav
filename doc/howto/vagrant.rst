=======
Vagrant
=======

Vagrant is a tool for easily create and configure lightweight, reproducible, and
portable development environments.

For this it uses a virtualization to create a virtual machine on top of a
VM provider (as of default, virtualbox).

.. _GettingStarted:

Getting started
---------------

* Download `VirtualBox <https://www.virtualbox.org/wiki/Downloads>`_

* Download `Vagrant <http://downloads.vagrantup.com/>`_

* Ensure `vagrant binaries` and `virtualbox binaries` is available in ``$PATH``

Run ``vagrant up`` in the root folder of your checked out source code.

Go fetch a coffee while waiting, this might take up to 15-30 minutes for the
first run as it is fetching a base debian image (approx 300MB) + install
lots of dependencies required for building every dependency from source!

Provisioning of VM is kicked of by :file:`VagrantFile` and launches
it's main bootstrap file :file:`tools/vagrant-provision.sh`.

This has some simple strict logic for kicking of `provioning` shell scripts
under :file:`tools/vagrant.d/`.

It's up and running, what now?
------------------------------

Installed datadirs and configuration files is placed under :file:`~vagrant/etc`
and :file:`~vagrant/var`.

Virtualenv is installed under :file:`~vagrant/.env`.

Source code is mounted inside the VM under :file:`/vagrant`

To get the webserver up and running you can issue ``rs`` which uses django's
manage.py to start runserver.

Please see Hacking with Pycharm for further details on how to setup our favorite
IDE which makes hacking on NAV much more fun!

If you want to learn about about the dirty details about the vagrant setup,
please referrer to the :doc:`/reference/vagrant` document.
