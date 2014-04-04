==============================
Vagrant provisioning reference
==============================

Vagrant is a tool for easily creating and configuring lightweight,
reproducible, and portable development environments using virtualization
technology.

For day-to-day usage of Vagrant in NAV development, please refer to
:doc:`using-vagrant`.

Provisioning scripts
--------------------

The Vagrant environment is configured in :file:`Vagrantfile`, which bootstraps
the VM using the :file:`tools/vagrant-provision.sh` provisioning script. This
script takes care of installing the necessary Debian packages, setting up a
virtualenv for NAV and installing the necessary Python requirements into this
virtualenv. The provisioning script will also run sub-provisioning scripts
from the :file:`tools/vagrant.d/` directory.

Sub-provisioning scripts
------------------------

The :file:`tools/vagrant.d/` directory contains various provisioning shell
scripts and *should* follow this strict naming pattern, to make sure they are
executed by the main provisioning script::

 <execution order number>-<executed as user in vm>-<script name>
     [0-9][0-9]u?                        [a-zaZ]*      [a-zaZ]*

Examples:

* :file:`10-vagrant-node.bash`
* :file:`15u-vagrant-vim.sh`

.. note:: The **u** suffix after the execution order number means this is a
          custom user provisioning script. This file pattern is ignored in
          NAV's :file:`.hgignore` file, and these files should not be
          committed to version control by force.

          For example, :file:`tools/vagrant.d/15u-vagrant-vim.sh` may be your
	  private shell provisioning script which installs your preferred
	  editor, :program:`vim`, and maybe checks out your `dotfiles
	  <http://dotfiles.github.io/>`_.

What provisioning scripts are doing
-----------------------------------

In this following section we will try to describe what the various
sub-provisioning scripts in :file:`tools/vagrant.d/` are doing, and why. To
make completely sure, you should just read the scripts themselves.

10-vagrant-node.bash
^^^^^^^^^^^^^^^^^^^^

This uses :program:`nvm` (`Node Version Manager`_) to install the latest
version of Node.js_ and its package manager :program:`npm`. :program:`nvm` can
install and manage multiple versions of Node.js

This script also installs the javascript testing libraries defined in
:file:`htdocs/js/package.json`. Please referr to :doc:`javascript`
for more information about hacking with JavaScript in NAV.

.. note:: Node.js and :program:`npm` is only used for installing the
          JavaScript testing libraries necessary for NAV development. You
          should probably **never** use :program:`npm` to install NAV
          requirements in a production environment.

.. _Node Version Manager: https://github.com/uninett-nav/nvm
.. _Node.js: http://nodejs.org


15-vagrant-user.sh
^^^^^^^^^^^^^^^^^^

This creates a default shell profile under :file:`~vagrant/.bash_profile`,
which in turn sets up the enviroment variables needed to work effectively with
NAV development in your VM (such as :envvar:`DJANGO_SETTINGS_MODULE`,
:envvar:`PYTHONPATH` and :envvar:`PATH`). It also ensures the virtualenv
installed in :file:`~vagrant/.env/` is activated on each login.

It also provides the alias ``rs`` for quickly starting the Django development
web server.

It then proceeds to install NAV's Python requirements (from
:file:`requirements.txt` and :file:`tests/requirements.txt`) using pip_.

The next step is to configure and build NAV from your source code, with
:makevar:`NAV_USER` set to ``vagrant`` and :makevar:`prefix` set to
:file:`/vagrant`. The latter ensures NAV runs "in-place", i.e. your source
code edits are live and available with a browser refresh button.

.. note:: Local state files (:makevar:`localstatedir`) and configuration files
          (:makevar:`sysconfdir`) are, however, installed in :file:`~vagrant/var` 
          and :file:`~vagrant/etc`, so you don't commit
          running state and configuration changes into version control by
          accident.

It also edits the installed :file:`nav.conf` to enable the ``DJANGO_DEBUG``
option, so that the web UI will throw full tracebacks in your face when you
create bugs.

.. _pip: http://www.pip-installer.org/

19-root-create_psql_vagrant_superuser.sh
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Creates a PostgreSQL superuser named ``vagrant``, so you don't have to muck
about with :program:`sudo` to do PostgreSQL administrative tasks in the VM.

20-vagrant-postgresql.sh
^^^^^^^^^^^^^^^^^^^^^^^^

Uses NAV's :file:`sql/syncdb.py` to populate the PostgreSQL database schema.

80-vagrant-set_nav_installed.sh
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Touches the file :file:`~vagrant/nav_installed`, which, if present, is a state
flag that indicates to :file:`tools/vagrant-provision.sh` that the initial
provisioning of NAV has been run already.

This ensures the ``make install`` step and PostgreSQL schema initialization is
skipped on subsequent reboots of the VM.

Base vagrant box image
----------------------

NAV targets the Debian platform, so it makes sense to use a Debian environment
for the VM. However, Vagrant's web site does not provide a Debian box image as
of this writing.

:file:`tools/build_vagrant_image.sh` can be used to build a minimal Debian
Stable box image for Vagrant, by using :program:`rvm` and
:program:`veewee`. You can read more about this in
:doc:`virtual-machines`.
