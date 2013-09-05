======================
Using Vagrant with NAV
======================

Vagrant_ is a tool for easily creating and configuring lightweight,
reproducible, and portable development environments using virtualization
technology.

For this, it uses a virtualization provider (by default: Virtualbox_) to
create and manage VMs.

.. _Vagrant: http://www.vagrantup.com/
.. _Virtualbox: http://www.virtualbox.com/

.. _Vagrant_Requirements:

Requirements
------------

Running Vagrant with Virtualbox requires that your CPU supports and has
enabled (in the BIOS) virtualization hardware extensions (VT-x/AMD-V), and
that it is otherwise capable of running a 64-bit operating system.

Failing to meet this requirement will cause the :kbd:`vagrant up` command to
fail or hang mysteriously. Using the Virtualbox GUI to boot VMs will, however,
most likely report the error properly.

Download and install the necessary software from the Virtualbox_ and Vagrant_
web sites.

It is important you ensure that the Vagrant and Virtualbox binaries are
available in your :envvar:`PATH` environment variable.


Getting started
---------------

In the root directory of your checked out NAV source code, run :kbd:`vagrant
up`.


.. tip:: Go get yourself a nice cup of coffee.

   The first time you run `vagrant up`, the virtual Debian enviroment must be
   bootstrapped, and this may take anywhere between 10 and 30 minutes to
   complete, depending on your Internet connection speed. A minimal Debian ISO
   (~300MB) will be downloaded and installed, then a bunch of dependencies for
   building and running NAV must be downloaded, built and installed to the VM.

The NAV Vagrant environment configuration is contained in
:file:`Vagrantfile`. The Vagrantfile specifies
:file:`tools/vagrant-provision.sh` as the main VM provisioning script, which
will be run in the VM each time you run `vagrant up`.

The provisioning script will also run further provisioning shell scripts from
the :file:`tools/vagrant.d/` directory. If you wish to add your own custom
provisioning scripts here, be sure to follow the script naming patterns
documented in :file:`tools/vagrant-provision.sh`.


It's up and running, what now?
------------------------------

SSH into your new virtual machine by typing :kbd:`vagrant ssh` in the root of
your checked out NAV source code.

Inside the VM, the root of your checked out NAV source code is mounted under
:file:`/vagrant`. NAV will be configured to run live from this directory,
except for the :makevar:`sysconfdir` and :makevar:`localstatedir` directories,
which respectively point to :file:`~vagrant/etc` and :file:`~vagrant/var`.

A Python virtualenv_ is installed under :file:`~vagrant/.env`, and has all of
NAV's Python requirements installed into it. This virtualenv is automatically
activated on login, in the `vagrant` user's shell profile.  This makes it easy
to test and change requirements during development.

.. note:: NAV's general policy on dependencies is that one should stick to
          dependencies that are already packaged by the official `Debian
          stable distribution
          <http://www.debian.org/distrib/packages#search_packages>`_! Any
          exceptions to this must be cleared with the lead developers before
          the code that introduces the dependency can be accepted into NAV.

Use the :kbd:`rs` command inside the VM to start the NAV web UI inside the
Django development web server. This command starts the web server on port
8080, which the :file:`Vagrantfile` forwards to you host OS port 8080 (meaning
you can access the web UI on your desktop machine as http://localhost:8080/).

The default administrator login/password in the web UI is: :kbd:`admin` /
:kbd:`admin`.

.. _virtualenv: http://www.virtualenv.org/

Other important things to know about Vagrant
--------------------------------------------

Unless you have a specific need to keep your VM running after your development
session, you should always make sure to shut down the VM by issuing
:kbd:`vagrant halt` in the project root.

If you have been *unlucky* and done things you maybe shouldn't have inside the
VM, and you are having difficulties reverting back to a working state, you can
always start over by issuing the :kbd:`vagrant destroy` command, which fully
destroys the VM. Before your start over, ensure you have a *backup* of any
changes you need that only exist inside the VM! There is no going back after
issuing :kbd:`vagrant destroy`. After destroying your VM, you can start over
simply by running :kbd:`vagrant up` again (and waiting for the full bootstrap
of a new VM).

If you have been playing with the provisioning scripts, or you need to run the
provisioning scripts over again, you can always issue :kbd:`vagrant provision`
to run them, without having to reboot your VM.

Further reading
^^^^^^^^^^^^^^^

If you want to learn the dirty details of NAV's Vagrant setup, read
:doc:`vagrant`.
