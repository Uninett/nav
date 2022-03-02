==============================================
Installing Graphite for use with NAV on Debian
==============================================

This is a short how-to guide for installing and configuring a simple Graphite
installation, dedicated to NAV, on a **Debian 10 (Buster)** or a **Debian 11
(Bullseye)** server.

.. warning:: **Do not start NAV** until you have properly configured your
             carbon-cache's storage schemas with NAV's provided storage schema
             config, or you *will* have issues with :doc:`blank areas in your
             graphs </faq/graph_gaps>`, which you will need to resolve
             manually after-the-fact.

A more `generic and up-to-date installation guide for Graphite
<https://graphite.readthedocs.io/en/latest/install.html>`_ can be found in the
Graphite project's own documentation.

Getting Graphite
================

A full Graphite setup consists of the *Carbon* backend server, which receives
metrics over TCP or UDP, and a *Graphite web frontend*, which enables browsing
and retrievial/rendering of the stored metrics. NAV will collect metrics and
send to the former, while utilizing the latter to retrieve metrics and render
graphs.

Assuming you will be running Graphite on the same Debian server as you are
running NAV, all you need to do to install Graphite on **Debian 10 or 11** is::

  apt-get install python3-psycopg2 graphite-carbon graphite-web

.. note:: Unfortunately, the ``graphite-web`` package has been removed from the
   official **Debian 11** distro. It is not clear why this happened, but it
   seems it will return in the next Debian stable release.

   We therefore provide a backported ``graphite-web`` package in NAV's official
   Debian APT repositories. If you don't already have this repository
   configured as a source in your Debian server, instructions to do so can be
   found at https://nav.uninett.no/install-instructions/#debian

Configuring Carbon
==================

Carbon, the metric-receiving backend of Graphite, must be configured before it
can be used with NAV. We will only be covering the simple case of using a
single *carbon-cache* process. Most of this information is adapted from the
:ref:`integrating-graphite-with-nav` section of the generic installation
documentation.

Edit :file:`/etc/carbon/carbon.conf` to ensure these options are set in the
``[cache]`` section:

.. code-block:: ini

   MAX_CREATES_PER_MINUTE = inf
   ENABLE_UDP_LISTENER = True

The first line ensures that Carbon will not delay creating Whisper backend
files for the metrics NAV sends it. The default setting is a maximum of 50
creates per minute (the setting exists to limit I/O strain on huge setups),
which means that when bootstrapping a NAV installation, hours to days can pass
before all its metrics are being actually stored in Graphite.

The second line ensures that Carbon accepts metrics on a UDP socket, which is
required by NAV.

Carbon also needs to know the resolution at which to store your time-series
data, for how long to store it, and how to roll up data from high resolution
data archives to lower resolution archives. These are the storage schemas and
aggregation methods. NAV provides its own config examples for this; on a
Graphite backend *dedicated to NAV*, you can simply symlink these config files
from NAV::

  cd /etc/carbon/
  mv storage-schemas.conf storage-schemas.conf.bak
  mv storage-aggregation.conf storage-aggregation.conf.bak
  ln -s /etc/nav/graphite/*.conf /etc/carbon/

Finally, restart the ``carbon-cache`` daemon::

  systemctl restart carbon-cache

Configuring the Graphite web interface
======================================

To enable the web interface, you need to do two things:

- Configure and create the database it will use for storing graph definitions.
- Configure Apache to serve the web interface.

Creating the graphite database
------------------------------

Graphite will by default use a SQLite database, but this is not recommended in
a production setting, as it will cause issues with multiple simultaneous
users. You already have a PostgreSQL installation because of NAV, so we
recommend using this.

Make a ``graphite`` PostgreSQL user and give it a password (make note of the
password), then create a database owned by that user::

  sudo -u postgres createuser --pwprompt --no-createrole --no-superuser --no-createdb --login graphite
  sudo -u postgres createdb --owner=graphite graphite

The Graphite web app's configuration file is located in
:file:`/etc/graphite/local_settings.py`. There are mainly three settings you
will need to adjust: ``SECRET_KEY``, ``TIME_ZONE`` and ``DATABASES``. The
``SECRET_KEY`` is used for cryptographic purposes when working with cookies and
session data (just as the ``SECRET_KEY`` setting from :file:`nav.conf`). It
should be a random string of characters; we can suggest using the
``makepasswd`` command to generate such a string:

.. code-block:: console

  $ makepasswd --chars 51
  iLNScMiUpNy5hditWAp9e2dyHGTFoX44UKsbhj91f9xL4fdJSDY

Then edit :file:`/etc/graphite/local_settings.py` (do not, under any
circumstances, re-use the actual example value of ``SECRET_KEY`` here!) and
make to set these three settings:

.. code-block:: python

   SECRET_KEY = 'iLNScMiUpNy5hditWAp9e2dyHGTFoX44UKsbhj91f9xL4fdJSDY'
   TIME_ZONE = 'Europe/Oslo' # This should correspond to your actual timezone, also as in nav.conf
   DATABASES = {
       'default': {
           'NAME': 'graphite',
           'ENGINE': 'django.db.backends.postgresql_psycopg2',
           'USER': 'graphite',
           'PASSWORD': 'the password you made note of above',
           'HOST': 'localhost',
           'PORT': '5432'
       }
   }


Now make ``graphite-web`` initialize its database schema::

  sudo -u _graphite graphite-manage migrate auth --noinput
  sudo -u _graphite graphite-manage migrate --run-syncdb --noinput

Configure Apache to serve the Graphite web app
----------------------------------------------

In principle, you can use any web server that supports the WSGI interface. You
should already have Apache with ``mod_wsgi`` installed, to serve NAV, so you
could use that. Alternatively, you can run Graphite (and even NAV, for that
matter), in a separate WSGI application server like uWSGI, and have Apache
proxy requests to the application server.

The two following examples will define an Apache virtual host that will serve
the Graphite web app on port **8000**. Adding SSL encryption is left as an
excercise for the reader (but should be unnecessary if you wisely choose to set
up the server to listen only to the localhost interface).

.. warning:: All graphite statistics will become browseable for anyone who can
             access your server on port 8000. You will probably want to
             restrict access to this port, either by using iptables or ACLs in
             your routers. Or, if you do not care about browsing the web app
             yourself, change the ``Listen`` statement into ``Listen
             127.0.0.1:8000``, so that only the NAV installation on
             ``localhost`` will be able to access it.


Option 1: Apache-based configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Graphite-web will need its own virtualhost, so let's add a new site config for
Apache (this example is inspired by the one supplied by the ``graphite-web``
package in :file:`/usr/share/graphite-web/apache2-graphite.conf`):

.. code-block:: apacheconf
   :caption: /etc/apache2/sites-available/graphite-web.conf

   Listen 8000
   <VirtualHost *:8000>

           WSGIDaemonProcess _graphite processes=1 threads=1 display-name='%{GROUP}' inactivity-timeout=120 user=_graphite group=_graphite
           WSGIProcessGroup _graphite
           WSGIImportScript /usr/share/graphite-web/graphite.wsgi process-group=_graphite application-group=%{GLOBAL}
           WSGIScriptAlias / /usr/share/graphite-web/graphite.wsgi

           Alias /content/ /usr/share/graphite-web/static/
           <Location "/content/">
                   SetHandler None
           </Location>

           ErrorLog ${APACHE_LOG_DIR}/graphite-web_error.log
           LogLevel warn
           CustomLog ${APACHE_LOG_DIR}/graphite-web_access.log combined

   </VirtualHost>


Option 2: uWSGI-based configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Graphite-web will still need its own virtualhost, but in this example, we will
we will run the app using a uWSGI container, and define an Apache virtual host
to proxy requests to this container.

First, install uWSGI and the necessary Apache modules to set up a uWSGI request
proxy::

  apt-get install uwsgi uwsgi-plugin-python3 libapache2-mod-proxy-uwsgi libapache2-mod-uwsgi

Then proceed to add a new uWSGI application definition:

.. code-block:: ini
   :caption: /etc/uwsgi/apps-enabled/graphite.ini

   [uwsgi]
   uid = _graphite
   gid = _graphite
   buffer-size = 32768
   chdir = /usr/share/graphite-web
   env = DJANGO_SETTINGS_MODULE=graphite.settings
   env = GRAPHITE_SETTINGS_MODULE=local_settings
   max-requests = 100
   module = graphite.wsgi:application
   plugins = python3
   processes = 5
   socket = 127.0.0.1:7999
   touch-reload = /usr/lib/python3/dist-packages/graphite/wsgi.py

To start an application container that will listen for requests on
``localhost:7999``, just run::

  systemctl restart uwsgi

Now you're ready to add an Apache site definition for this app:

.. code-block:: apacheconf
   :caption: /etc/apache2/sites-available/graphite-web.conf

   Listen 8000
   <VirtualHost *:8000>
	   Alias /static/ /usr/share/graphite-web/static/
	   <Location "/static/">
		   SetHandler None
		   Require all granted
	   </Location>
	   <Location "/">
		   Options FollowSymlinks Indexes
		   Require all granted
	   </Location>

	   ErrorLog ${APACHE_LOG_DIR}/graphite-web_error.log
	   LogLevel warn
	   CustomLog ${APACHE_LOG_DIR}/graphite-web_access.log combined

	   ProxyRequests Off
	   ProxyPreserveHost Off

	   # Let Apache serve static files
	   ProxyPass /static/ !
	   ProxyPassReverse /static/ !
	   # Give the rest to our uWSGI instance
	   ProxyPass / uwsgi://127.0.0.1:7999/
	   ProxyPassReverse / uwsgi://127.0.0.1:7999/

	   ProxyTimeout 300
   </VirtualHost>

Then make sure to enable the required Apache modules to use this site config::

  a2enmod uwsgi proxy proxy_uwsgi


Finally, in both configuration options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Enable the new site on port 8000::

  a2ensite graphite-web
  systemctl restart apache2


Congratulations, you should now be ready to start NAV!
