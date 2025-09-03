=======================================
Using devcontainers for NAV development
=======================================

NAV provides a `devcontainer <https://containers.dev/>`_ definition to simplify
the process of creating a complete environment for running and developing
NAV. This should integrate smoothly with popular IDEs like PyCharm and VS
Code. There are also command line tools to interact with devcontainers for
those who prefer not to use IDEs for development, but we don't yet have any
experience with these.

What is provided by the NAV devcontainer
========================================

The devcontainer definition resides in the :file:`.devcontainer/` directory and
uses `Docker Compose`_ to provide three containers:

1. The main devcontainer, ``nav``, which should be provisioned with all
   dependencies normally required to build and run NAV from source code.
2. A PostgreSQL service container (``db``) to provide relational database
   services to NAV.
3. A Graphite service container (``graphite``) to provide both the back-end
   (``carbon``) and front-end (``graphite-web``) components that provide time
   series database services to NAV.

Working efficiently with the ``nav`` devcontainer
=================================================

Tools like PyCharm and VS Code should automatically detect the devcontainer
definitions when you open the NAV project in them. They should typically prompt
you and ask if you want to start the devcontainer and re-open the IDE inside
it.

The devcontainer only provides an environment for development, it doesn't do
much magic in the background.

TL;DR
-----

1. Open a terminal inside the devcontainer.  Issue these commands to start the
   web server::

     navsyncdb
     django-admin runserver

2. Open a second terminal inside the devcontainer. Issue this command to start
   all NAV background processes::

     sudo nav start

3. Open a third terminal inside the devcontainer. Issue this command to
   automatically build all CSS stylesheets when the SASS sources change::

     make sasswatch

4. Open a fourth terminal inside the devcontainer. Issue this command to
   automatically build the HTML documentation output when the source file
   change::

     make docwatch


Python environment
------------------

The Python environment inside the devcontainer is a *virtualenv* located in
:file:`/home/vscode/.venv`, and the :file:`/home/vscode/.venv/bin/` directory
is automatically pre-pended to the container's :envvar:`PATH` environment
variable, so that any program inside this environment is available and
automatically executed within said environment.

The environment is built at container startup by `uv`_, using the :samp:`uv
sync --all-extras` command.  This ensures that all runtime requirements and
development dependency groups mentioned in NAV's :file:`pyproject.toml` should
be installed into the environment.

Using :samp:`uv sync` also ensures that all NAV command line programs are
available on the :envvar:`PATH` search path, and that changes you make to their
source code is immediately reflected when running them. If you add new NAV
command programs, however, you may need to run :samp:`uv sync --all-extras`
over again, to ensure their stubs are installed in the environment's
:file:`bin/` directory.


Configuring NAV
---------------

At startup, the container installs all of NAV's example configuration files
into the :file:`/home/vscode/.venv/etc/nav/` directory. This can be confirmed
at any time by issuing the :samp:`nav config where` command in a terminal
inside the container.

NAV's :file:`db.conf` configuration file is automatically imbued with the
options necessary to let NAV connect to the PostgreSQL server in the ``db``
container.

The container also provides common text editors like :program:`vim` and
:program:`nano`, which should enable you to edit the configuration files if
necessary.

Configuring JWT signing keys for the API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are working with the API, the script :file:`tools/reset-jwt-keys.sh` can
be used to quickly generate new RSA signing keys and configure NAV to use them.
See :ref:`local-jwt-configuration` for more details.


Preparing the database schema
-----------------------------

When you start the devcontainer for the first time, the database may be
completely empty.  You will need to run the :samp:`navsyncdb` command in order
to initialize and/or migrate NAV's database schema, before any NAV programs are
usable within the container.


Running the NAV web interface
-----------------------------

When developing, the NAV web interface is best served by the built-in Django
development web server, using this command in a terminal: :samp:`django-admin
runserver`.

This server will serve on port *8000* inside the container. After running this
command, your IDE may prompt you to forward this port to your host machine, so
you will be able to browse the web site from your desktop browser (in some
cases, it may automatically forward port 8000 also to your localhost).

Logging in to the NAV web interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``admin`` user ships with the default password ``admin``. If you need to
test with unprivileged users, more can be added using the *User and API
Administration* tool in the toolbox.

User accounts and passwords can also be manipulated on the command line using
the :program:`navuser` program (see :ref:`navuser usage docs <navuser-usage>`
for details).


Running NAV programs
--------------------

NAV command line programs (those specified by the ``project.scripts`` section
of :file:`pyproject.toml`) are all available on :envvar:`PATH` and can be run
directly if need be.  The :program:`nav` process control command is also
available, so that all background daemons and cron jobs can be started by
issuing the :samp:`sudo nav start` command.

During certain development tasks, it may be preferable to manually run specific
daemon programs in the foreground rather than using the :program:`nav` command,
e.g. :samp:`ipdevpolld -f -s` instead of :samp:`nav start ipdevpolld`.


(Re)building CSS stylesheets from SASS sources
----------------------------------------------

If you make changes to the SASS definitions, you will have to execute
:samp:`make sassbuild` to rebuild the CSS assets that are served by the web
server.

More effectively, you may want to use the :samp:`make sasswatch` command, which
will monitor all the SASS source files for changes and automatically rebuild
the stylesheets on every change.


(Re)building NAV's Sphinx documentation
---------------------------------------

NAV's documentation sources reside in the :file:`doc/` directory. These can be
manually built into HTML using the :samp:`make doc` command. The output
directory is automatically served by the Django development web server on the
``/doc/`` URI.

More effectively, you may want to use the :samp:`make docwatch` command, which
will monitor all the documentation source files for changes and automatically
rebuild the HTML output on every change.


Installing Python packages manually
-----------------------------------

If you want to install extra Python packages that are not specified in
:file:`pyproject.toml`, use :samp:`uv pip install {package_name}` to do so.

Please be aware, though, that these packages will potentially be removed any
time :samp:`uv sync` is rerun.  If a package is a new runtime dependency for
code you're working on, it should be added to the ``project.dependencies`` list
of :file:`pyproject.toml` ASAP.  If it's a development tool that is nice or
necessary to have, it should be added to the relevant dependency groups in
the ``dependency-groups`` section of :file:`pyproject.toml`.


Dumping/loading data from remote production server
--------------------------------------------------

For some development tasks, it is useful to initialize the development database
with a database snapshot from a production server. You can read more about
:ref:`migrating_prod_db_to_dev`.


IPv6 connectivity
=================

NAV is fully capable of working over IPv6, but Docker is not usually configured
to work with IPv6 out-of-the-box. This presents a challenge if you need to
communicate with devices over IPv6 while developing inside the
devcontainer. Fortunately, since `Docker version 27`_, IPv6 has become a lot
easier to configure.

The NAV devcontainer definition already places all the service containers (as
defined in :file:`.devcontainer/docker-compose.yml`) on a separate IPv6-enabled
network. This network is configured with IPv6 masquerading, to ensure that your
service containers are not exposed on the public IPv6 network.

To enable IPv6 in your Docker daemon, you will need to add something like the
following stanza to your Docker system's :file:`daemon.json` and restart the
Docker daemon:

.. code-block:: json

   {
       "ipv6": true,
       "fixed-cidr-v6": "fd00::/80",
       "default-network-opts": {
           "bridge": {
               "com.docker.network.enable_ipv6": "true"
           }
       }
   }

.. tip:: The location of :file:`daemon.json` may vary between systems and
         setups (you may even need to create it yourself). Please refer to
         Docker's own `documentation on how to configure the Docker daemon
         <https://docs.docker.com/engine/daemon/#configure-the-docker-daemon>`_.

To test IPv6 connectivity from within the devcontainer (assuming this already
works from your host system), you can open a terminal and run something like
:code:`ping6 -c 4 google.com`:

.. code-block:: console

  vscode ➜ /workspaces/nav (doc/devcontainer-ipv6) $ ping6 -c 4 google.com
  PING google.com(arn09s22-in-x0e.1e100.net (2a00:1450:400f:801::200e)) 56 data bytes
  64 bytes from arn09s22-in-x0e.1e100.net (2a00:1450:400f:801::200e): icmp_seq=1 ttl=110 time=38.8 ms
  64 bytes from arn09s22-in-x0e.1e100.net (2a00:1450:400f:801::200e): icmp_seq=2 ttl=110 time=39.4 ms
  64 bytes from arn09s22-in-x0e.1e100.net (2a00:1450:400f:801::200e): icmp_seq=3 ttl=110 time=39.1 ms
  64 bytes from arn09s22-in-x0e.1e100.net (2a00:1450:400f:801::200e): icmp_seq=4 ttl=110 time=39.1 ms

  --- google.com ping statistics ---
  4 packets transmitted, 4 received, 0% packet loss, time 3006ms
  rtt min/avg/max/mdev = 38.753/39.087/39.399/0.228 ms

  vscode ➜ /workspaces/nav (doc/devcontainer-ipv6) $


PyCharm oddities
================

PyCharm seems to have problems with properly detecting the correct Python
interpreter when running inside the devcontainer. When started, it lists the
project as having *no interpreter*, and the only way to fix it is to manually
select an existing interpreter (specifically,
:file:`/home/vscode/.venv/bin/python`). Unfortunately, this choice does not
seem to be persisted anywhere, so every time PyCharm is re-opened inside the
container, this interpreter selection procedure needs to be repeated.



.. _Docker Compose: https://docs.docker.com/compose/
.. _Docker version 27: https://docs.docker.com/engine/release-notes/27/#ipv6
.. _uv: https://docs.astral.sh/uv/
