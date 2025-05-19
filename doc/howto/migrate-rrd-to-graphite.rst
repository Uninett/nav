######################################################
 Migrating RRD data to Graphite (from NAV 3 to NAV 4)
######################################################

When upgrading from NAV 3 to NAV 4, you may want to keep historic traffic
graphs and other time-series data collected into RRD files by NAV 3 and
Cricket.

NAV 4.0 through 4.5 comes with a utility for converting NAV 3 RRD files into Whisper_ files
(Whisper_ is the data format used by Graphite). This how-to documents usage of
the utility and limitations of the conversion process.


.. warning:: You cannot upgrade directly from NAV 3 to 4.6 and keep your RRD
             data. You will either have make a decision to lose your old RRD
             data, or perform an intermediary upgrade via an NAV 4 version.


*****
TL;DR
*****

On the NAV server, run this program::

  migrate_to_whisper.py <PATH>

where `PATH` is the directory where your whisper file hierarchy will be
placed.

* If your Graphite Carbon backend runs on the same server as NAV, this
  can point directly to its whisper storage directory (most commonly
  :file:`/opt/graphite/storage/whisper/`).
* If not, specify a temporary directory and move the files to your Carbon server.


**********
Conversion
**********

Assumptions before we start:

* You have stopped NAV 3 and installed NAV 4.
* You have installed and configured Graphite according to
  :ref:`integrating-graphite-with-nav`.
* :mod:`py-rrdtool` must still be installed on the NAV server, as well as
  :mod:`whisper`.
* You have **NOT** started NAV 4.

On the NAV server, run this program::

  migrate_to_whisper.py <PATH>

where `PATH` is the directory where your whisper file hierarchy will be
placed.

* If your Graphite Carbon backend runs on the same server as NAV, this
  can point directly to its whisper storage directory (most commonly
  :file:`/opt/graphite/storage/whisper/`).
* If not, specify a temporary directory and move the files to your Carbon
  server afterwards.

When conversion is complete and the Whisper files are on the target server,
ensure they are readable/writable by the user that runs the Carbon daemon
(e.g. :code:`chmod -R graphite:graphite /opt/graphite/storage/whisper/nav`).

Runtime considerations
~~~~~~~~~~~~~~~~~~~~~~

Conversion may take a long time to complete, depending on the amount of data
you have to convert. We have only one data point so far:

On a reasonably modern computer (Intel i7 Quad core with 8GB RAM, an SSD and a
64-bit OS), converting *2512* RRD files to Whisper took approximately 19
minutes. This is from a small NAV installation with only 39 monitored IP
devices and 108 monitored subnet prefixes on 63 VLANs.


Converting while NAV 4 is running
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you start NAV 4 before proceeding with the RRD conversion, NAV will begin
to send metrics to Graphite; the Whisper files the conversion tool wants to
produce will therefore already exist in Carbon's storage directory.

Any Whisper files that already exist will not be overwritten by the conversion
tool, but they will be *updated* with old data from the RRD file (aka.
"backfilling"). You may think this will help you avoid downtime data gaps in
your resulting graphs, **but** because of the precision mismatches detailed in
the :ref:`rrd-migration-data-archives-mismatch` section, you may get multiple
gaps in older data instead.

.. note:: If you cannot live with this downtime, you can opt to start NAV 4
          and have the conversion tool place Whisper files in a temporary
          directory. When the conversion process is over, you can overwrite
          the Whisper files in Carbon's storage directory with those produced
          by NAV. You will, of course, still have the downtime gap in your
          graphs, but NAV will at least monitor and dispatch alerts as usual
          during the conversion.


Migrating between different platforms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The RRD file format is platform/architecture dependent, whereas Whisper files
are not. If you are attempting to migrate your RRD data to a new NAV server,
the two servers' architectures must match. If they don't, you must run the
conversion step on the original server (a typical scenario is migrating from a
32-bit platform to a 64-bit platform).

Your only other option in the face of an architecture mismatch is to dump the
RRD files to XML files on the original server, and then load those back into
RRD files on the new server.

If you choose the latter option, things can get complicated quick. Here's a
suggestion that has been employed by the authors of NAV (and requires the
`rrdtool` command line program to be present on both servers):

1. Put the following shell script on your original NAV server, as
   :file:`/root/migrate-rrd.sh`, and make sure it is executable:

   .. code-block:: bash

      #!/usr/bin/env bash

      list_nav_rrdfiles() {
	sudo -u postgres psql nav -P format=unaligned -q -t -c "SELECT path || '/' || filename FROM rrd_file"
      }

      list_nav_rrdfiles | while read RRD
      do
	  TARGET=".$RRD"
	  TARGETDIR=`dirname "$TARGET"`
	  echo "mkdir -p \"$TARGETDIR\""
	  echo "rm -f \"$TARGET\""
	  echo "cat << EOF | rrdtool restore - \"$TARGET\""
	  rrdtool dump $RRD
	  echo "EOF"
      done

2. On the new NAV-server, run the following:

   .. code-block:: bash

      cd /
      ssh root@oldnavserver /root/migrate-rrd.sh | bash

   This will make the old NAV server produce a stream of shell commands to
   load RRD files from XML and put these in the same paths as the originals.
   Piping these commands to a `bash` shell will execute them on the new
   server.

   .. warning:: Yes, we know this is an ugly hack; make sure you make a backup
                of everything, **don't run this as root** if you can help it,
                and don't blame us if anything goes wrong.


***********
Limitations
***********

.. _rrd-migration-data-archives-mismatch:

Data archives
~~~~~~~~~~~~~

What _rrdtool refers to as a Round Robin Archive (RRA) corresponds to what
Whisper_ calls a "retention archive". Each archive stores data points at a
specific time resolution, for a specific period of time.

Conventional wisdom says "recent data is more interesting than old data",
meaning one wants high resolution on recent data, but low resolution on old
data is OK. The convention is to have multiple archives covering increasing
periods of time with decreasing resolution.

NAV ships with a Graphite/Carbon config file with recommended storage schemas
for NAV data. The precisions and lengths of the defined retention archives
will in some instances deviate from those used in NAV 3's RRD files; some data
will be stored at higher precision in NAV 4 compared to NAV 3.

For practical resons, the conversion tool will mirror the RRAs in RRD files as
retention archives in the Whisper files it creates, regardless of this
configuration. However, the highest precision archives are important, so if
the recommended precision in NAV 4 is higher than what the old RRD file
provides, the tool will create a higher precision archive and interpolate data
from RRD into this.

Any new metrics collected by NAV will be subject to the storage schemas
configured in Carbon.

Whisper comes with `command line tools`_ for altering/adding retention
archives in existing Whisper files, if you wish to make changes
after-the-fact. A common wish is to retain data for longer periods than the
default - these tools would enable that.


Aggregation methods
~~~~~~~~~~~~~~~~~~~

What _rrdtool refers to as "consolidation functions" corresponds to what
Whisper_ calls "aggregation methods".

In an RRD file, consolidation functions are an attribute of each RRA, meaning
you can have multiple, overlapping archives which consolidate data points in
different ways. In Whisper, the aggregation method is an attribute of the
Whisper file itself.

NAV 3 may have RRD files with overlapping archives to include `maximum` and
`average` consolidation of the same data points. The default of the NAV 4
Graphite setup is to use the `average` aggregation for Whisper files. The
conversion tool will therefore only extract the average values from the RRD
files.


Network interface counter discontinuities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

NAV 3's RRD files use DERIVE-based data sources for interface counters (octet,
packet and error counters, etc.), meaning the values stored in the RRD files
are the actual traffic data rates. Whisper does not support DERIVE-type
calculations at insert time, so NAV 4 will instead store the raw counter
values in Graphite, and convert to rates when presenting graphs/data.

The rates stored in RRD files will therefore be converted to absolute counter
values when inserted into the corresponding Whisper files. Unless there is a
gap between the converted data and the new data collected by NAV 4, this may
result in huge spikes in your graphs at the point in time you converted.


Environmental sensor precision changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some environmental sensor values are reported at a specific decimal precision.

NAV versions prior to 4.0 would configure Cricket to store raw values into the
RRD files (meaning a Celsius temperature value of 314 with a precision of 1
would be stored as 314, not as 31.4, which is the actual temperature value).

NAV 4.0 will scale the values according to their precision before storing in
Graphite. The conversion tool will, however, not scale old values from RRD
files. Any sensor metric graphs with a decimal precision point will have a
visible scale-related jump at the point in time you converted.


.. _Whisper: https://graphite.readthedocs.org/en/latest/whisper.html
.. _`command line tools`: https://github.com/graphite-project/whisper
.. _rrdtool: http://oss.oetiker.ch/rrdtool/
