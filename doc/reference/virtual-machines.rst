================
Virtual Machines
================

We use virtual machines to make it easy for either you as a ``developer`` to
install a developer environment for NAV or if you want to deploy a ``production
ready`` virtual appliance.

In NAV we uses `rvm <https://github.com/uninett-nav/rvm>`_ ,
`veewee <https://github.com/uninett-nav/veewee>`_ and virtualbox to create base
images to be used for virtualization.

In this reference document you will get an introduction on how to use the
developers tools residing under :file:`tools/` to build VM images.

You can read more about `vagrant` in :doc:`howto </howto/vagrant>` and
:doc:`reference </reference/vagrant>` documents.

Ruby Version Manager (rvm)
--------------------------

"RVM is a command-line tool which allows you to easily install, manage, and work
with multiple ruby environments from interpreters to sets of gems."
-- http://rvm.io/

Since ``veewee`` requires ruby and is the leading tool for creating customized
virtual images we uses it powerful magic to help us to do so.

rvm is the equivalent of virtualenv, just a bit more complicated..

Anyhow, we have the :file:`tools/rvm_and_veewee_install.sh` script which helps
us install a custom `rvm` install under :file:`tools/.rvm` instead of
interfering of your personal private install under ``$HOME/.rvm`` if you use rvm
personally.

To install rvm you will need the following dependencies from apt:

::

 sudo apt-get install gawk g++ libreadline6-dev zlib1g-dev libssl-dev libyaml-dev libsqlite3-dev sqlite3 autoconf libgdbm-dev libncurses5-dev automake libtool bison libffi-dev bash curl patch bzip2 ca-certificates gcc make libc6-dev patch openssl ca-certificates libreadline6 curl zlib1g pkg-config

And for veewee you will need these following dependencies from apt:

::

 sudo apt-get install libxml2-dev libxslt1-dev

After installation it uses ``source`` :file:`tools/rvm_activate` to activate
 the installed ``rvm`` environment.

Next step by the installer is to install ``veewee`` which it does by cloning
veewee's repository to :file:`tools/veewee/`

The installer script then uses the gem `bundler` to install ruby dependencies
locally under the :file:`tools/veewee/`.

Build vagrant image
-------------------

:file:`tools/build_vagrant_image.sh` fetches the default Debian stable (wheezy)
template to ``preseed`` an debian install. The script ensures to use the
Norwegian debian mirror for faster install.

The image is so exported as ``nav-basevm`` and you will find the ``.box image``
to be placed under :file:`tools/veewee/nav-basevm.box` after a successful build.


Build virtual appliance
-----------------------

:file:`tools/build_virtual_appliance.sh` uses the veewee templates residing
inside :file:`tools/veewee-templates.d/nav-debian-virtual-appliance/`.
These are based on the original debian stable (wheezy) templates available from
veewee.

The important provisioning script which does most of the ``preseeding`` of the
virtual appliance is
:file:`tools/veewee-templates.d/nav-debian-virtual-appliance/pressed.cfg` which
installs NAV dependencies from apt.

:file:`tools/veewee-templates.d/nav-debian-virtual-appliance/nav.sh` continues
the installation process and uses the
`Debian package <http://pkg-nav.alioth.debian.org/>`_ packed for NAV by
Morten Werner Forsbring.

It also have scripts to execute the instructions as
of defined in the :file:`README.Debian` and also changes the default memory
allocation for the virtual appliance to 2048 MB which is the minimum
requirements.