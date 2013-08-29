=======
Vagrant
=======

Vagrant is a tool for easily create and configure lightweight, reproducible, and
portable development environments.

Provisioning scripts
--------------------

The bootstrap is kicked of by :file:`VagrantFile` executing
:file:`tools/vagrant-provision.sh` which installs dependencies from Debian
and kicks of sub-provisioning scripts which resides in :file:`tools/vagrant.d/`

tools/vagrant.d/
----------------

Files in vagrant.d/ is shell provisioning scripts and ``should`` follow this
strict syntax:

::

 <execution order>-<executed as user in vm>-<script name>
     [0-9][0-9]u?         [a-zaZ]*            [a-zaZ]*

Examples:

* 10-vagrant-node.bash
* 15u-vagrant-vim.sh

``NOTE``: the suffix of '`u`' after `execution order` means this is a user
provided script which should not be added in NAVs repository!

NAVs repository have a `default ignore` for ``user provided scripts`` as we're
having a ``.hgignore`` entry for `[0-9][0-9]u*` files residing inside
:file:`tools/vagrant.d`!

For example the :file:`tools/vagrant.d/15u-vagrant-vim.sh` will be your private
shell provisioning script which installs vim and maybe checks out your
`dotfiles <http://dotfiles.github.io/>`_

What provisioning scripts are doing
-----------------------------------

In this following section we will try to describe why we have the following
provisioning scripts as we have under :file:`tools/vagrant.d/`.

For even better understanding of the provisioning scripts, you should probably
simply read em all ;-)

tools/vagrant.d/10-vagrant-node.bash
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This uses a tool called `nvm <https://github.com/uninett-nav/nvm>`_ to crawl
node's homepage to be able to fetch and install a version of ``node`` with it's
following package manager ``npm``.

``nvm`` is capable of installing multiple versions of node and set which version
should be the default one.

This script also installs the javascript testing libraries defined in
:file:`htdocs/js/package.json` . Please referrer to :doc:`/reference/javascript`
for more information about hacking with Javascript in NAV.

You ``should`` note that node is only used for installing javascript testing
libraries and it is ``important`` you ``do not`` use `npm` to install required
dependencies for running NAV in production!

tools/vagrant.d/15-vagrant-user.sh
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It create a default shell profile under :file:`~vagrant/.bash_profile` which
ensures you have correct environment variables for ``DJANGO_SETTINGS_MODULE``,
``PYTHON_PATH`` and ``PATH`` and ``activates the virtualenv`` installed under
:file:`~vagrant/.env/`.

It also provides a default alias ``rs`` for quickly booting up the webserver
with django's management command runserver.

In the continue to install all of NAVs dependencies using
`pip <http://www.pip-installer.org/en/latest/>_` where the dependencies is
specified in :file:`requirements.txt` and :file:`tests/requirements.txt`.

Next step is to run the necessary build steps by autogen/make to install NAV
with ``NAV_USER`` set to vagrant and prefix set to /vagrant where the source
code is residing so you can do inplace updating of templates and simply do a
refresh in your webbrowser to see the code changes.

``Data files`` (/var (variable data files)) and ``configuration files`` (/etc)
is installed under :file:`~vagrant/var`and :file:`~vagrant/etc` so you can run
NAV and configure settings without having to worry about committing changes to
the repository.

It also enables ``DJANGO_DEBUG`` as of default, you are a developer when using
vagrant ;-)

tools/vagrant.d/19-root-create_psql_vagrant_superuser.sh
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Creates a super user in postgresql for the user vagrant.

tools/vagrant.d/20-vagrant-postgresql.sh
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Uses NAVs :file:`sql/syncdb.py` to populate the postgresql database.

tools/vagrant.d/80-vagrnat-set_nav_installed.sh
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

touches a file in :file:`~vagrant/nav_installed` which is read by
:file:`tools/vagrant-provision.sh`. This is simply to provide sub-provisioning
scripts with a state if the provisioning has been run before.

You want to skip certain steps as ``make install`` or other things to make
provisioning run faster any other ``vagrant up`` after the first initialized
boot up.

Base vagrant box image
----------------------

As NAV targets the Debian platform, it was needed to provide a base box image
for Debian as `vagrant` does not ship by default a Debian box image.

:file:`tools/build_vagrant_image.sh` is used for building a minimal Debian
Stable box image by using ``rvm`` and ``veewee``. You can read more about
this in :doc:`/reference/virtual-machines`.