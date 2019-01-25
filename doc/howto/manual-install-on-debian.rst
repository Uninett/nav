===============================
 Install from source on Debian
===============================

This details what the Debian package does for you automatically.
Adapt this if you can't use an official ``.deb`` or need to install on
something that isn't Debian-based.

.. note:: This howto is based on Debian 9 (Stretch).

1. Get the source
=================

Get the source::

  git clone https://github.com/Uninett/nav.git

You might want to choose your version now, otherwise you'll be installing the
bleeding edge `master` branch. All release versions have git tags, so you can
easily find and checkout the latest stable version.


2. OS dependencies
==================

Debian Stretch already comes with *Python 2.7*, so no need to touch that.

First get the following OS packages::

  apt-get install -y python-pip python-wheel git postgresql
  apt-get install -y libpq-dev libjpeg-dev libz-dev libldap2-dev libsasl2-dev


3. NAV/Python dependencies
==========================

To install NAV's Python requirements::

  pip install -r requirements.txt

4. Install NAV itself
=====================

cd into the :file:`nav/` directory you got from git, then run::

  pip install .
  nav config install /etc/nav

The configuration files are now found in :file:`/etc/nav/`.

5. Build the docs
=================

If you like, you can build the complete HTML documentation thus::

    python setup.py build_sphinx

6. Verify that NAV can find its main configuration file
=======================================================

::

    nav config where

7. Initialize the database
==========================

In :file:`/etc/nav/db.conf` there should be a line starting with
``userpw_nav``. Choose a password and append it here, then run::

    sudo -u postgres navsyncdb -c

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

Take note of the path (:file:`/usr/share/nav/www/static`) as you'll need it in the
next step and type :kbd:`yes` and hit :kbd:`Enter`.

This will copy static files (css, javascripts, images, fonts and similar) into
the path.


9. Configure Apache
===================

Copy the file :file:`/etc/nav/apache/apache.conf.example` to
:file:`/etc/nav/apache/apache.conf` and edit the defines inside the copy.

* ``documentroot`` should be the path from step 8.
* ``documentation_path`` is where Sphinx put the docs, in
  ``$SOURCE_CODE_DIRECTORY/build/sphinx/html/``.

Leave the rest.

Inside a ``VirtualHost``-directive, add:

.. code-block:: apacheconf

  ServerName nav.example.org
  ServerAdmin webmaster@example.org

  Include /etc/nav/apache/apache.conf

.. important:: You should always protect your NAV web site using SSL!

10. Create users and groups
===========================

Create a ``navcron`` user and a corresponding group for NAV to run as::

  sudo addgroup --system nav
  sudo adduser --system --no-create-home --home /usr/local/nav \
               --shell /bin/sh --ingroup nav navcron

You should also make sure `navcron` has permission to write log files, pid
files and various other state information. You can configure the log and pid
file directories in :file:`nav.conf`. Then make sure these directories exist
and are writable for the ``navcron`` user::

  sudo chown -R navcron:nav /path/to/log/directory
  sudo chown -R navcron:nav /path/to/pid/directory

Sending SMS messages using a locally attached GSM device
--------------------------------------------------------

If you want to use NAV's SMS functionality in conjunction with Gammu, you
should make sure the ``navcron`` user is allowed to write to the serial device
you've connected your GSM device to. Often, this device has a group ownership
set to the ``dialout`` group, so the easieast route is to add the ``navcron`` user
to the ``dialout`` group::

  sudo addgroup navcron dialout


11. Installing and configuring Graphite
=======================================

NAV uses Graphite_ to store and retrieve time-series data. A `somewhat outdated
guide for installing Graphite for use with NAV on a Debian system can be found
in the wiki <https://nav.uninett.no/wiki/graphite_on_debian>`_.  This guide
will be updated and included in the official documentation.

.. _Graphite: http://graphite.readthedocs.org/

12. Start using NAV
===================

You should now move on the the :doc:`/intro/getting-started` guide.
