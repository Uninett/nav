==========================
Manual install from source
==========================

This details what the debian package does for you automatically. Adapt this if
you can't or won't use an official .deb.

1. Get the source
=================

Get the source::

  git clone https://github.com/Uninett/nav.git

cd into the directory created, named ``nav``.

2. OS dependencies, exmplified by stretch
=========================================

First get the following OS pacakges::

  apt-get install -y python-pip python-wheel git postgresql

See the ``Dockerfile`` for other OS dependencies to be installed with ``apt``.
Note the build dependencies!

The list changes often enough that the Dockerfile has the canonical answer.

3. NAV dependencies
===================

Python requirements::

  pip install -r requirements.txt

4. Install NAV itself
=====================

cd into the nav directory you got from git then run::

  pip install .
  nav config install /etc/nav

The config-files are now in ``/etc/nav``.

5. Build the docs
=================

::

    python setup.py build_sphinx

6. Verify that NAV can find its main configuration file
=======================================================

::

    nav config where

7. Initialize the database
==========================

In ``/etc/nav/db.conf`` there should be a line starting with ``userpw_nav``. Append a password here, then run::

    navsyncdb -c

You should now have a database ``nav`` with a user ``nav``.

8. Install the static resources
===============================

Run::

    django-admin collectstatic --settings=nav.django.settings

It'll respond with something like::

    You have requested to collect static files at the destination
    location as specified in your settings:

        /usr/share/nav/www/static

    This will overwrite existing files!
    Are you sure you want to do this?

    Type 'yes' to continue, or 'no' to cancel:

Take note of the path (``/usr/share/nav/www/static``) as you'll need it in the
next step and type "yes" and hit Enter.

This will copy static files (css, javascripts, images, fonts and similar) into
the path.


9. Configure apache
===================

Copy the file ``/etc/nav/apache/apache.conf.example`` somewhere apache is allowed to read it.

Edit the defines inside the copy.

* ``documentroot`` should be the path from step 8.
* ``documentation_path`` is where Sphinx put the docs, in
  ``$SOURCE_CODE_DIRECTORY/build/sphinx/html/``.

Leave the rest.

.. _creating-users-and-groups:
10. Create users and groups
===========================

::

  sudo addgroup --system nav
  sudo adduser --system --no-create-home --home /usr/local/nav \
               --shell /bin/sh --ingroup nav navcron;

NAV processes should run as a non-privileged user, whose name is configurable
in :file:`nav.conf` (the default value being ``navcron``). Preferably, this
user should also have a separate system group as well.

If you want to use NAV's SMS functionality in conjunction with Gammu, you
should make sure the `navcron` user is allowed to write to the serial device
you've connected your GSM device to. Often, this device has a group ownership
set to the `dialout` group, so the easieast route is to add the `navcron` user
to the dialout group::

  sudo addgroup navcron dialout

You should also make sure `navcron` has permission to write log files, pid
files and various other state information. You can configure the log and pid
file directories in :file:`nav.conf`. Then make sure these directories exist
and are writable for the ``navcron`` user::

  sudo chown -R navcron:nav /path/to/log/directory
  sudo chown -R navcron:nav /path/to/pid/directory
