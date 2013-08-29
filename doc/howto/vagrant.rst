=======
Vagrant
=======

Vagrant is a tool for easily create and configure lightweight, reproducible, and
portable development environments.

For this it uses a virtualization to create a virtual machine on top of a
VM provider (as of default, virtualbox).

.. _GettingStarted:

Requirements
------------

First of all you need to check if you have the following requirements to run
up a virtual machine by ``vagrant`` using ``virtualbox`` as the VM provider.

This requires your CPU supports the ``virtual machine bit (vt-x/AMD-V)`` and
is capable of running a 64-bit operating system. The failure of not checking
this is that ``vagrant up`` will stand spinning and never be able to boot up the
virtual machine. (if you enable the VM-provider GUI, you will most likley see
an error message that your lacking support for the virtual machine bit.)

After confirming you support the `virtual machine bit`, continune to fetch and
install the following softwares:

* `VirtualBox <https://www.virtualbox.org/wiki/Downloads>`_

* `Vagrant <http://downloads.vagrantup.com/>`_

It is important you ensure ``vagrant binaries`` and ``virtualbox binaries`` is
available in your environment variable ``$PATH`` which is used by all common
operating systems to search for executables  without specifying full path to the
binaries.

Getting started
---------------

You have now installed `VirtualBox` which NAV uses as the default VM provider in
`vagrant`.

Open up a ``command prompt`` and ``enter the directory`` where you have checked
out ``NAV VCS (version control system) root``.

Run ``vagrant up`` and now be patient!

Go fetch a coffee while waiting, this might take up to 15-30 minutes for the
first run as it is fetching a base Debian image (approx 300MB) and installing
lots of dependencies required for building every dependency from source in a
python `virtualenv`!

Provisioning of VM is kicked of by :file:`VagrantFile` and launches
it's main bootstrap file :file:`tools/vagrant-provision.sh`.

This has some simple strict logic for kicking of `provisioning` shell scripts
under :file:`tools/vagrant.d/`. The format of file names is documented in
:file:`tools/vagrant-provision.sh` if you need to update/create new provisioning
files.

It's up and running, what now?
------------------------------

To enter the virtual machine, you can type ``vagrant ssh`` in the root of your
checked out source files which will ssh into the virtual machine.

Installed datadirs and configuration files is placed under :file:`~vagrant/etc`
and :file:`~vagrant/var` away from VCS root.

Source code is mounted `inside the VM` under :file:`/vagrant`

`Virtualenv` is installed under :file:`~vagrant/.env` and should be used as the
python interpreter. This is by default `activated` by the shell's login profile
for the vagrant user.

This makes it easy to test/change dependencies, but it is important to
understand that NAV restrict our requirements for dependencies to libraries
available in
`Debian Stable <http://www.debian.org/distrib/packages#search_packages>`_!

To get the webserver up and running you can issue ``rs`` `inside the VM` which
uses django's manage.py to start runserver on port 8080 which is port-forwarded
in :file:`Vagrantfile`. In simpler words you should be able to access the web
by entering ``http://localhost:8080`` in your browser.

The default administrator credentials in the web interface is: admin / admin.

For further setup and easier hacking on NAV, we highly suggest
:doc:`/howto/hacking-with-pycharm` for further details on how to setup our
favorite IDE which makes hacking on NAV much more fun!

Other important things to know about vagrant
--------------------------------------------

After your development session you should always make sure to shutdown the VM
by issuing ``vagrant halt`` in the project root. This cleanly shut downs the VM.

If you have been `unlucky` and done things you maybe shouldn't have done in the
VM and you have difficulties reverting back to a working state, you could always
start over by issuing the ``vagrant destroy`` command which fully destroy the VM
. Ensure you have ``backup`` of your changes if you want to start over! There is
no going back after issuing ``vagrant destroy``. After issuing the command you
simply start over again by ``vagrant up`` which does default setup as it was the
first time booting up the VM.

If you have been playing with the `provisioning` scripts, or you need to run the
provisioning scripts again, you can always issue ``vagrant provision`` to run em
without having to reboot your VM.
(they are also run every time you run ``vagrant up`` for your information!)

If you want to learn about about the dirty details about the vagrant setup,
please referrer to the :doc:`/reference/vagrant` document.

This document goes into details for what the provisioning scripts are doing,
and how everything is setup. So if you want to embrace yourself with more
knowledge, take a tripe to :doc:`reference/vagrant`, it is highly recommended!
:-)
