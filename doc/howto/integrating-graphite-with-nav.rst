.. _integrating-graphite-with-nav:

Integrating Graphite with NAV
-----------------------------

.. highlight:: ini

NAV uses :xref:`Graphite` to store and retrieve/graph time-series data. Installing
Graphite itself is out of scope for this guide, but assuming you already have *a
complete installation of Graphite*, you need to change some configuration
options in both Graphite and NAV to ensure your time-series data is stored and
retrieved properly:

1. NAV needs to know the details of *where to send data*.
2. NAV needs to know the details of *how to retrieve time-series data* from
   :program:`graphite-web` (Graphite's front-end web service for retrieving stored
   data)
3. :program:`carbon-cache` (Graphite's backend component for receiving and
   storing time series data) needs to know **how** it should store data
   received from NAV.

Configuring NAV
~~~~~~~~~~~~~~~

NAV must be configured with the IP address and port of your Graphite
installation's Carbon backend, and the URL to the Graphite-web frontend used
for graphing. These settings can be configured in the :file:`graphite.conf`
configuration file.

.. note:: NAV requires the Carbon backend's UDP listener to be enabled, as it
          will only transmit metrics over UDP.

For a simple, local Graphite installation, you may not need to touch this
configuration file at all, but at its simplest it looks like this::

  [carbon]
  host = 127.0.0.1
  port = 2003

  [graphiteweb]
  base = http://localhost:8000/


Configuring Graphite
~~~~~~~~~~~~~~~~~~~~

You will need to make some configuration changes to :program:`carbon-cache`
before letting NAV send data to Graphite:

1. First and foremost, you will need to enable the UDP listener in the
   configuration file :file:`carbon.conf`.

   For performance reasons, Carbon will also limit the number of new Whisper
   files that can be created per minute. This number is fairly low by default,
   and when starting NAV for the first time, it may send a ton of new metrics
   very fast. If the limit is set to 50, it will take a long time before all
   the metrics are created. You might want to increase the
   ``MAX_CREATES_PER_MINUTE`` option, or *temporarily* set it to ``inf``.

2. You should add the suggested *storage-schema* configurations for the
   various ``nav`` prefixes listed in :file:`etc/graphite/storage-schemas.conf`:

   .. literalinclude:: ../../python/nav/etc/graphite/storage-schemas.conf

   The highest precision retention archives are the most important ones here,
   as their data point interval must correspond with the collection intervals
   of various NAV processes. Other than that, the retention periods and the
   precision of any other archive can be freely experimented with.

   Remember, these schemas apply to new Whisper files as they are created. You
   should not start NAV until the schemas have been configured, otherwise the
   Whisper files will be created with the global Graphite defaults, and your
   data may be munged or inaccurate, and your graphs will be spotty.

3. You should add the suggested *storage-aggregation* configurations listed in
   the file :file:`etc/graphite/storage-aggregation.conf`:

   .. literalinclude:: ../../python/nav/etc/graphite/storage-aggregation.conf

   These will ensure that time-series data sent to Graphite by NAV will be
   aggregated properly when Graphite rolls them into lower-precision archives.

Ensure :program:`carbon-cache` is restarted to make these changes take effect,
before adding devices to monitor in your NAV installation.

.. _PostgreSQL: https://www.postgresql.org/
