========================
Virtual Machines and NAV
========================

Virtualization technology makes working with NAV development much easier. It
also enables user's to try out NAV quickly, using virtual appliances.

NAV's source code includes scripts for working with NAV in virtual machines,
either for development, or for producing an :abbr:`OVF (Open Virtualization
Format)`-based virtual appliance running NAV.

These scripts use rvm_, veewee_ and :program:`Virtualbox` to create base
images to be used for virtualization.

In this reference document you will get an introduction to using these
scripts (from the :file:`tools/` directory) to build VM images.

You can read more about Vagrant in :doc:`using-vagrant` and
:doc:`vagrant`.

.. _rvm: https://github.com/uninett-nav/rvm
.. _veewee: https://github.com/uninett-nav/veewee


Ruby Version Manager (rvm)
--------------------------

.. epigraph::

   RVM is a command-line tool which allows you to easily install, manage, and
   work with multiple ruby environments from interpreters to sets of gems.
 
   -- http://rvm.io/

Since :program:`veewee` requires :program:`Ruby`, and is the leading tool for
creating customized virtual images, we use its powerful magic to help us do
exactly that.

:program:`rvm` is the equivalent of Python's `virtualenv`, just a bit more
complicated.

The :file:`tools/rvm_and_veewee_install.sh` script can be used to install a
custom `rvm` environment under :file:`tools/.rvm` (instead of interfering with
any personal enviroment in :file:`~/.rvm` you may have if you are already an
`rvm` user).

To install `rvm` on a **Debian-based OS**, you will need the following
dependencies (!):

.. code-block:: sh

   sudo apt-get install gawk g++ libreadline6-dev zlib1g-dev libssl-dev \
                        libyaml-dev libsqlite3-dev sqlite3 autoconf \
                        libgdbm-dev libncurses5-dev automake libtool bison \
                        libffi-dev bash curl patch bzip2 ca-certificates gcc \
                        make libc6-dev patch openssl ca-certificates \
                        libreadline6 curl zlib1g pkg-config

And for `veewee` you will need the following dependencies:

.. code-block:: sh

   sudo apt-get install libxml2-dev libxslt1-dev

:file:`tools/rvm_and_veewee_install.sh` will install and activate the
mentioned `rvm` environment.  Next, it will proceed to checkout `veewee`
directly from its `git` repository into :file:`tools/veewee`. The gem
`bundler` will then be used to install its Ruby dependencies into the same
directory.


Building a  Vagrant box image
-----------------------------

The :file:`tools/build_vagrant_image.sh` script downloads a minimal Debian
Wheezy ISO image (netboot) and installs it with a custom `preseed`
configuration to produce a Debian template for Vagrant.

.. note:: The script will configure the preseed file with a Norwegian Debian
          mirror, since most NAV developers are located in Norway. You can of
          course change this to your liking if you want.

The template is exported as ``nav-basevm``, which you will find as
:file:`tools/veewee/nav-basevm.box` after a successful build.


Build a virtual appliance
-------------------------

The :file:`tools/build_virtual_appliance.sh` script uses the `veewee`
templates in :file:`tools/veewee-templates.d/nav-debian-virtual-appliance/`.
These are based on the original Debian Wheezy templates available from
`veewee`.

The preseed config used for building the appliance is
:file:`tools/veewee-templates.d/nav-debian-virtual-appliance/preseed.cfg`.

:file:`tools/veewee-templates.d/nav-debian-virtual-appliance/nav.sh`
provisions the VM with a NAV installation based on `the latest stable Debian
package <http://pkg-nav.alioth.debian.org/>`_ maintained by Morten Werner
Forsbring.

The virtual appliance is also automatically provisioned according to the
instructions from the NAV package's :file:`README.Debian` file, while the
default memory allocation for the virtual appliance is set to to a suitable
minimum of *2048MB*.
