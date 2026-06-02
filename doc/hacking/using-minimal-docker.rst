.. _minimalist-docker-dev:

================================================================
Running just the database and graphite in Docker for development
================================================================

Instead of running everything including NAV and a live rebuild of the docs via
``docker compose``, it is possible to just run the database and graphite.

There are helper commands in the Makefile.

The docker compose config used is in ``tools/local-dev/docker-compose.yml``.

Make-helpers
============

``make local-setup``
--------------------

This sets up the docker containers and the virtualenv. The virtualenv used is
the one in ``.venv``. If there already is a ``.venv`` (for instance from
using the previous ``docker compose`` workflow), move it out of the way first.

``make local-up``
-----------------

Starts this ``docker compose``. The port 5434 is used for postgres, the port
2003 is used for graphite. You can set the environment variable ``NAV_PG_PORT``
to run postgres on an alternative port.

``make local-down``
-------------------

Shuts down this ``docker compose`` configuration and frees the ports.

How to configure NAV
====================

The etc-files are in ``.venv/etc/nav``.

How to test
===========

You can run tox directly, even for integration tests!

::

        $ tox

How to run NAV
==============

::

        $ django-admin runserver

Starts NAV, on port 8000.

Troubleshooting
===============

Cannot access the database
--------------------------

This is usually caused by the environment not having been set correctly.

Check if the the file ``sitecustomize.py`` exists in the distro-installed
Pythons (Ubuntu does this). This overrides the ``sitecustomize.py`` that is
created by ``make local-setup``.

You can either remove the global ``sitecustomize.py`` or set the environment
variables some other way, see
``.venv/lib/python*/site-packages/sitecustomize.py`` for what variables to
set.

``django-admin`` not found
==========================

Most likely you've activated the wrong virtualenv. Deactivate the one you have::

        $ deactivate

then activate the correct one. Be in the root of the repo::

        $ source .venv/bin/activate
