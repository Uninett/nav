=====================================
Using NAV with Docker for development
=====================================

.. highlight:: sh

Docker is a lightweight "virtualization" framework for creating isolated
environments, useful both in development and production.
For more information on Docker visit their homepage_ or read the documentation_.

Installing Docker and docker-compose
------------------------------------

Docker has updated documentation on how to install it for most Linux
distributions [*]_.

.. Tip:: To avoid having to use sudo with docker commands, it is recommended
         to add your user to the ``docker`` group. You may need to relogin for it to
         take effect.

Building the Docker image
-------------------------

First you will need to obtain the NAV source code.

The source contains a configuration file for `Docker Compose`_ to build a
suite of containers for PostgreSQL, Graphite and NAV itself. Simply run this
command to build and run everything::

    docker-compose up

.. Tip:: The first time you run this would be the perfect time to grab some
         coffee (and maybe redecorate your living room), as the initial build
         may take a while.


Using the container(s)
----------------------

The Docker Compose specificiation creates these containers (called "services"
in Docker Compose lingo):

nav
  This container runs the NAV backend processes and cron jobs. It also runs the
  "sass-watcher" job, which will watch ``*.scss`` files for modifications and
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

  docker-compose exec nav /bin/bash

Manually restarting the web server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To manually restart the web server, all you need is::

  docker-compose restart web

Rebuilding the NAV code from scratch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A complete rebuild of the NAV code can be initiated by::

  docker-compose restart nav

Rebuilding the containers
~~~~~~~~~~~~~~~~~~~~~~~~~

If you are switching between branches, though, you may need to rebuild the
images the containers are based on (as different development branches may have
different requirements, and therefore different Dockerfiles). Stop the existing
containers and run this::

  docker-compose build


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
  This is a process that monitors the :file:`python/nav/web/sass/` subdirectory
  for changes, and re-runs ``python setup.py build_sass`` (i.e. rebuilding all
  the SASS-based stylesheets) on changes.

The individual logs of these program are typically found inside the ``nav``
container in the :file:`/var/log/supervisor/` directory. The NAV process logs
themselves are placed inside the :file:`/tmp/` directory inside the ``nav``
container.

Controlling log levels
----------------------

The log levels of various parts of NAV are controlled through the config file
:file:`/etc/nav/logging.conf` inside the containers. Please be aware that the
``nav`` and ``web`` containers do not share a configuration volume, so you may
need to make adjustments in either container, depending on your needs.


Overriding the compose services
-------------------------------

If you need to override certain aspects of the Docker Compose service
definitions for your own purposes during development, you can usually do so
without patching the :file:`docker-compose.yml` file. You can "patch" the
definitions via `Docker Compose's override mechanism`_: Simply add a
:file:`docker-compose.override.yml` to the top-level source directory.

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


Happy hacking!


.. [*] See https://docs.docker.com/install/
.. _homepage: https://docker.com
.. _documentation: https://docs.docker.com/
.. _Docker Compose: https://docs.docker.com/compose/gettingstarted/
.. _Docker Compose's override mechanism: https://docs.docker.com/compose/extends/
