=====================================
Using NAV with Docker for development
=====================================

.. highlight:: sh

Docker is a lightweight "virtualization" framework for creating isolated
environments, useful both in development and production.
For more information on Docker visit their homepage_ or read the documentation_.

Installing Docker and docker compose
------------------------------------

Docker provides up-to-date documentation on how to install it for most popular
operating systems [*]_.  NAV's Docker definitions should work smoothly on
Linux, but may have some rough edges on Docker Desktop for Mac.

.. Tip:: To avoid having to use sudo with docker commands, it is recommended
         to add your user to the ``docker`` group. You may need to relogin for it to
         take effect.

Getting started with Docker Compose
-----------------------------------

After installing Docker, you will need to obtain the NAV source code.

The source code contains a :file:`docker-compose.yml` configuration file for
`Docker Compose`_.  This configuration defines a fully integrated NAV runtime
environment, with all its dependencies.  This environment is designed to run
NAV directly from the checked out source code, and as such it defines an
environment for developers, not for production use of NAV.  The alternative is
to manage all the dependencies and integrations on your own host machine.

.. tip:: Be mindful that :doc:`a devcontainer-based solution
         <using-devcontainers>` is largely superseding this way of working with
         NAV development—at least for developers who prefer using IDEs.

The quickest way to build the container images and start all the services for
the first time is by running these commands::

    make .env
    docker compose up

.. Tip:: The first time you run this would be the perfect time to grab some
         coffee (and maybe redecorate your living room), as the initial build
         may take a while.

.. warning:: Running ``docker compose up`` will take over the local ports 80
             (for the website) and 8000 (for graphite). You can override this
             with a ``docker-compose.override.yml`` file.

Troubleshooting
~~~~~~~~~~~~~~~

The container images for NAV development are designed to bind-mount your source
code directory inside the running containers.  In order to avoid leaving files
owned by strange user IDs in your source code directory, the images will create
a non-privileged ``nav`` user with a specific user-id and group-id.  These IDs
should match that of your user account on the host system, so therefore the
Docker Compose build process needs to know your ``UID`` and ``GID``.

.. note:: This UID/GID mapping is not really relevant if you are running Docker
          Desktop on a Mac, since it uses an entirely different mechanism for
          bind-mounted volumes.  You still will need to set the ``UID`` and
          ``GID`` arguments for the build to work, though.

The quickest way to go about this is the :code:`make .env` command.  This will
attempt to generate a :file:`.env` file in your top-level source code
directory, which will set the ``UID`` and ``GID`` variables from your running
environment.  Docker Compose will implicitly read the environment variables in
this file when it builds or runs the services defined in
:file:`docker-compose.yml`.  If, for some reason, the :code:`make .env` command
does not work for you, you can create the :file:`.env` file by hand (but supply
real values if you're on Linux):

.. code-block:: shell
   :caption: :file:`.env` example

   UID=1337
   GID=100


Using the container(s)
----------------------

The Docker Compose specificiation creates several containers (called "services"
in Docker Compose lingo).  Several of them will mount the checked out source
code directory internally on the `/source` directory, allowing them to always
be up-to-date with the latest changes you are making in your favorite editor.

These are the defined services:

nav
  This container runs the NAV backend processes and cron jobs. It also runs the
  ``sass-watcher`` job, which will watch ``*.scss`` files for modifications and
  recompile NAV's CSS when changes do occur.

web
  This container runs the Django development server to serve NAV's web-based
  user interface. By default, Docker Compose will expose this web service on
  port 80 on the host system, i.e. at http://localhost/

postgres
  This runs a bog standard Postgres image from the Docker Hub, to serve as
  NAV's main data store.

graphite
  This runs both carbon-cache backend and a graphite-web frontend, for NAV's
  storage and retrieval of time-series data. By default, Docker Compose will
  expose the web service on port 8000 on the host system,
  i.e. http://localhost:8000/

docbuild
  This container will watch the :file:`doc/` directory for changes and initiate
  a rebuild of the NAV documentation whenever the documentation source files
  are modified. The built documentation should normally be browseable via the web
  service at http://localhost/doc/

Accessing internals of running containers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If need be, you can access the internals of the running containers (to control
NAV daemons using the ``nav`` command, adjust the running config, or whatever)
by running a bash shell inside the container, like so (for the ``nav``
container)::

  docker compose exec nav /bin/bash

Manually restarting the web server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To manually restart the web server, all you need is::

  docker compose restart web

Rebuilding the NAV code from scratch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A complete rebuild of the NAV code can be initiated by::

  docker compose restart nav

Rebuilding the containers
~~~~~~~~~~~~~~~~~~~~~~~~~

Running :code:`docker compose up` will normally build the container images,
before starting them, if they don't exist already.  However, if the image
definitions have changed (e.g. when you are switching between development
branches or changed the :file:`Dockerfile` definitions, or any of the files
used as part of the image definitions), you may need to rebuild the images.  To
initiate a full build (which will still utilize Docker's build cache), run
this::

  docker compose build

Another valid method is to use the ``--build`` option when starting the
containers.  This will ensure the images are always rebuilt if necessary as
part of the startup process::

  docker compose up --build

Sometimes, you may find that a rebuild isn't enough to clear out all the cruft
after switching development branches or adding or changing NAV's default
configuration file examples.  The Docker Compose environment defines two
persistent volumes that will retain their data between restarts and rebuilds:
``nav_cache`` and ``nav_config``.  The former exist just to share some caching
data between the various service containers.  The second ensures the set of NAV
config files remain persistent between restarts or rebuilds, and also that all
service containers can share the same set of files.  When you really want to
start from scratch, you can fully nuke the Docker Compose environment and the
persistent volumes using this command (before initiating a new ``up`` or
``build`` command)::

  docker compose down --volumes


Controlling processes inside the nav container
----------------------------------------------

The main ``nav`` container uses :program:`supervisord` to control multiple
processes. While the ``nav`` command can be used to control individual NAV
services, :program:`supervisorctl` can be used to control other processes used
within the development environment:

cron
  This is the regular system cron daemon, responsible for running recurring NAV
  tasks.

nav
  This is a one-time supervisor task to start all of NAV when the container
  starts.

sass-watcher
  This is a process that runs ``npm run watch:sass`` command to monitor and
  rebuild all the SASS-based stylesheets whenever changes occur
  in the :file:`python/nav/web/sass/` subdirectory. The command continuously
  monitors the files and does not exit by itself.

The individual logs of these program are typically found inside the ``nav``
container in the :file:`/var/log/supervisor/` directory. The NAV process logs
themselves are placed inside the :file:`/tmp/` directory inside the ``nav``
container.

Controlling log levels and configuration
----------------------------------------

The log levels of various parts of NAV are controlled through the config file
:file:`/etc/nav/logging.conf` inside the containers.

The ``nav`` and ``web`` containers share a common configuration volume named
``nav_config``. This volume should persist even between rebuilds of the
containers themselves. If you want NAV to install a completely new set of
config files from scratch, you may need to manually trash this volume using the
``-v`` option to the :code:`docker compose down` command.

Viewing logs
------------

Running ``docker compose up`` will output everything from every container to
standard out, interleaving logs from different containers and sub-systems. You
can instead run docker compose in the background with ``docker compose -d`` and
get logs from a specific service with ``docker compose logs -f SERVICENAME``.

You can also enter a specific container with ``docker compose exec SERVICENAME
/bin/bash`` and ``tail -f`` a log-file directly. The logs are by default stored
in ``/tmp`` inside the container.

Location of frontend logs
~~~~~~~~~~~~~~~~~~~~~~~~~

The logs of the frontend (generated by python via the ``logging`` module) ends
up in the ``web``-container, not the ``nav``-container.

Overriding the compose services
-------------------------------

If you need to override certain aspects of the Docker Compose service
definitions for your own purposes during development, you can usually do so
without patching the :file:`docker-compose.yml` file. You can "patch" the
definitions via `Docker Compose's override mechanism`_: Simply add a
:file:`docker-compose.override.yml` to the top-level source directory.


Dumping/loading data from remote production server
--------------------------------------------------

For some development tasks, it is useful to initialize the development database
with a database snapshot from a production server. You can read more about
:ref:`migrating_prod_db_to_dev`.


Preventing NAV backend services from starting at container startup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can add the environment variable ``NONAVSTART=1`` to prevent the backend
daemons from being started at the ``nav`` container startup time (allowing for
complete manual control of daemons, by entering the container using ``exec``,
as documented above). This can be done by adding something akin to this:

.. code-block:: yaml
   :caption: docker-compose.override.yml

   version: '2'
   services:
     nav:
       environment:
         - NONAVSTART=1

The same technique can be used to insert your own environment into the ``web``
container.

Debugging via logging
---------------------

Set log level to DEBUG in ``/etc/nav/logging.conf``::

   [levels]
   nav = DEBUG

You can suppress logs from a subsystem by setting it to NOTSET::

   [levels]
   nav.arnold = NOTSET

You might also want to send logs for a specific subsystem to a specific file::

   [files]
   nav.ipdevpoll.plugins = ipdevpoll-plugins.log

Happy hacking!


.. [*] See https://docs.docker.com/install/
.. _homepage: https://docker.com
.. _documentation: https://docs.docker.com/
.. _Docker Compose: https://docs.docker.com/compose/gettingstarted/
.. _Docker Compose's override mechanism: https://docs.docker.com/compose/extends/
