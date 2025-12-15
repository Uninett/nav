===============================
 Install from source on Debian
===============================

.. highlight:: sh

This details what the Debian package does for you automatically.
Adapt this if you can't use an official ``.deb`` or need to install on
something that isn't Debian-based.

.. note:: This howto is based on Debian 9 (Stretch).

1. OS dependencies
==================

First get the following OS packages::

  apt-get install -y python-pip python-wheel git postgresql apache2 libapache2-mod-wsgi libsnmp30


2. Get the source
=================

Get the source::

  git clone https://github.com/Uninett/nav.git
  cd nav

You might want to choose your version now, otherwise you'll be installing the
bleeding edge `master` branch. All release versions have git tags, so you can
easily find and checkout the latest stable version (although these instructions
are not valid for versions of NAV prior to 4.9). Use ``git tag`` to list the
available tags, and ``git checkout x.y.z`` to checkout version ``x.y.z``.


3. NAV/Python dependencies
==========================

To install NAV's Python requirements::

  apt-get install -y libpq-dev libjpeg-dev libz-dev libldap2-dev libsasl2-dev
  pip install -r requirements.txt -c constraints.txt

4. Install NAV itself
=====================

::

  pip install .
  nav config install /etc/nav

.. tip::

   You can override the default configuration search path by setting the
   :envvar:`NAV_CONFIG_DIR` environment variable to point to a directory
   containing your NAV configuration files. When set, this directory will be
   searched with highest priority, before any of the default locations.

The configuration files are now found in :file:`/etc/nav/`. Verify that NAV can
actually find :file:`nav.conf`::

  nav config where

5. Build the docs
=================

If you like, you can build the complete HTML documentation thus::

    sphinx-build


6. Initialize the database
==========================

In :file:`/etc/nav/db.conf` there should be an option called
``userpw_nav``. Choose a password and append it here, then run::

    sudo -u postgres navsyncdb -c

You should now have a database ``nav`` with a user ``nav``.


7. Create users and groups
==========================

Create a ``navcron`` user and a corresponding group for NAV to run as::

  sudo addgroup --system nav
  sudo adduser --system --home /usr/share/nav \
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


8. Ensure that a writeable uploads directory exists
===================================================

The NAV web ui allows you to upload and attach images to room and location
objects. These images will be stored in the file system, so NAV needs a
writeable directory to store them in (and from where the web server can serve
them).

We suggest::

  mkdir -p /usr/share/nav/var/uploads
  chown navcron:nav /usr/share/nav/var/uploads

Then, ensure you set this option in :file:`nav.conf`::

  UPLOAD_DIR=/usr/share/nav/var/uploads


9. Install the static resources
===============================

Run::

    django-admin collectstatic --settings=nav.django.settings

It'll respond with something like:

.. code-block:: console

    You have requested to collect static files at the destination
    location as specified in your settings:

        /usr/share/nav/www/static

    This will overwrite existing files!
    Are you sure you want to do this?

    Type 'yes' to continue, or 'no' to cancel:

Take note of the path (:file:`/usr/share/nav/www`, without the ``static``
subdir), as you'll need it in the next step and type :code:`yes` and hit
:kbd:`Enter`.

This will copy static files (css, javascript, images, fonts and similar) into
that path.


10. Configure Apache
====================

Copy the file :file:`/etc/nav/apache/apache.conf.example` to
:file:`/etc/nav/apache/apache.conf` and edit the defines inside the copy.

* ``documentroot`` should be the path from step 9.
* ``documentation_path`` is where Sphinx put the docs, in
  ``$SOURCE_CODE_DIRECTORY/build/sphinx/html/``.
* ``nav_uploads_path`` is the upload path you created in step 8.
* ``nav_python_base`` should be :file:`/usr/local/lib/python3.9/dist-packages` (or wherever the ``nav`` Python module was installed)

We suggest creating a new Apache site config:
Inside a ``VirtualHost``-directive, add:

.. code-block:: apacheconf
   :caption: /etc/apache2/sites-available/nav.conf

   <VirtualHost *:80>
       ServerName nav.example.org
       ServerAdmin webmaster@example.org

       Include /etc/nav/apache/apache.conf
   </VirtualHost>

You should, of course, replace ``nav.example.org`` with a DNS name that your
server can actually be reached under.

Then, disable the default Apache site, enable the ``nav`` site, and enable
``mod_wsgi``, before restarting Apache::

  a2dissite 000-default
  a2ensite nav
  a2enmod wsgi
  systemctl reload apache2

You should now be able to browse the NAV web interface.

.. important:: You should always protect your NAV web site using SSL!



11. Installing and configuring Graphite
=======================================

NAV uses :xref:`Graphite` to store and retrieve time-series data. If you do not
already have a Graphite installation you wish to integrate with NAV, here is a
:doc:`separate guide on how to install and use Graphite with NAV on your Debian
system </howto/installing-graphite-on-debian>`.


Start using NAV
===============

You should now be ready to move on the the :doc:`/intro/getting-started` guide.
