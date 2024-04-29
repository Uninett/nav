===================================
Setting up FreeRADIUS to log to NAV
===================================

The module has been tested to run on the following:

* NAV 3.4
* FreeBSD 6.2
* FreeRADIUS 1.1.7
* PostgreSQL 8.2.5
* Firefox 2/3


Installing the accounting module
--------------------------------

Step 1: Configuring FreeRADIUS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

<path to freeradius>/etc/raddb/postgresql.conf
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following needs to be set:

=============== ================================================================
``server``      Hostname to your server running the PostgreSQL DB
``login``       The name of the user you granted INSERT and UPDATE
                privilege to on the radius accounting table.
``password``    Password.
``radius_db``   This will be ``nav`` for a typical NAV install
``acct_table1`` Must be set to ``radiusacct``
``acct_table2`` Same as above. FreeRADIUS lets you log Start and Stop
                packets to different tables, but we don't make use of this.
=============== ================================================================

The accounting queries in this file also needs to be replaced, since we have
messed around a bit with the default setup of the table. Replace them with
these::

        accounting_onoff_query = "UPDATE ${acct_table1} \
                SET AcctStopTime = (now() - '%{Acct-Delay-Time:-0}'::interval), \
                AcctSessionTime = (EXTRACT(EPOCH FROM(now()::timestamp with time zone - AcctStartTime::timestamp with time zone - '%{Acct-Delay-Time:-0}'::interval)))::BIGINT, \
                AcctTerminateCause='%{Acct-Terminate-Cause}', AcctStopDelay = '%{Acct-Delay-Time:-0}' \
                WHERE AcctSessionTime IS NULL AND AcctStopTime IS NULL AND NASIPAddress= '%{NAS-IP-Address}' AND AcctStartTime <= now()"


        accounting_update_query = "UPDATE ${acct_table1} \
                SET FramedIPAddress = NULLIF('%{Framed-IP-Address}', '')::inet, \
                AcctSessionTime = (EXTRACT(EPOCH FROM(now()::timestamp with time zone - AcctStartTime::timestamp with time zone - '%{Acct-Delay-Time:-0}'::interval)))::BIGINT, \
                AcctInputOctets = (('%{Acct-Input-Gigawords:-0}'::bigint << 32) + '%{Acct-Input-Octets:-0}'::bigint), \
                AcctOutputOctets = (('%{Acct-Output-Gigawords:-0}'::bigint << 32) + '%{Acct-Output-Octets:-0}'::bigint) \
                WHERE AcctUniqueId = '%{Acct-Unique-Session-Id}' AND UserName = '%{SQL-User-Name}' \
                AND NASIPAddress= '%{NAS-IP-Address}' AND AcctStopTime IS NULL"

        accounting_update_query_alt = "INSERT into ${acct_table1} \
                (AcctSessionId, AcctUniqueId, UserName, Realm, NASIPAddress, NASPortType, CiscoNASPort, AcctStartTime, \
                AcctSessionTime, AcctInputOctets, AcctOutputOctets, CalledStationId, CallingStationId, \
                FramedProtocol, FramedIPAddress) \
                values('%{Acct-Session-Id}', '%{Acct-Unique-Session-Id}', '%{SQL-User-Name}', '%{Realm}', '%{NAS-IP-Address}', \
                '%{NAS-Port-Type}', NULLIF('%{Cisco-NAS-Port}', ''), (now() -  '%{Acct-Delay-Time:-0}'::interval - '%{Acct-Session-Time:-0}'::interval), \
                NULLIF('%{Acct-Session-Time}','')::bigint, \
                (('%{Acct-Input-Gigawords:-0}'::bigint << 32) + '%{Acct-Input-Octets:-0}'::bigint), \
                (('%{Acct-Output-Gigawords:-0}'::bigint << 32) + '%{Acct-Output-Octets:-0}'::bigint), '%{Called-Station-Id}', \
                '%{Calling-Station-Id}', '%{Framed-Protocol}', \
                NULLIF('%{Framed-IP-Address}', '')::inet)"

        accounting_start_query = "INSERT into ${acct_table1} \
                (AcctSessionId, AcctUniqueId, UserName, Realm, NASIPAddress, NASPortType, CiscoNASPort, AcctStartTime, \
                CalledStationId, CallingStationId, FramedProtocol, FramedIPAddress, AcctStartDelay) \
                values('%{Acct-Session-Id}', '%{Acct-Unique-Session-Id}', '%{SQL-User-Name}', '%{Realm}', '%{NAS-IP-Address}', \
                '%{NAS-Port-Type}', NULLIF('%{Cisco-NAS-Port}', ''), (now() - '%{Acct-Delay-Time:-0}'::interval), \
                '%{Called-Station-Id}', '%{Calling-Station-Id}', '%{Framed-Protocol}', \
                NULLIF('%{Framed-IP-Address}', '')::inet, '%{Acct-Delay-Time:-0}') "

        accounting_start_query_alt  = "UPDATE ${acct_table1} \
                SET AcctStartTime = (now() - '%{Acct-Delay-Time:-0}'::interval) \
                WHERE AcctUniqueId = '%{Acct-Unique-Session-Id}' AND UserName = '%{SQL-User-Name}' \
                AND NASIPAddress = '%{NAS-IP-Address}' AND AcctStopTime IS NULL"

        accounting_stop_query = "UPDATE ${acct_table2} \
                SET AcctStopTime = (now() - '%{Acct-Delay-Time:-0}'::interval), \
                AcctSessionTime = NULLIF('%{Acct-Session-Time}', '')::bigint, \
                AcctInputOctets = (('%{Acct-Input-Gigawords:-0}'::bigint << 32) + '%{Acct-Input-Octets:-0}'::bigint), \
                AcctOutputOctets = (('%{Acct-Output-Gigawords:-0}'::bigint << 32) + '%{Acct-Output-Octets:-0}'::bigint), \
                AcctTerminateCause = '%{Acct-Terminate-Cause}', AcctStopDelay = '%{Acct-Delay-Time:-0}', \
                FramedIPAddress = NULLIF('%{Framed-IP-Address}', '')::inet \
                WHERE AcctUniqueId = '%{Acct-Unique-Session-Id}' AND UserName = '%{SQL-User-Name}' \
                AND NASIPAddress = '%{NAS-IP-Address}' AND AcctStopTime IS NULL"

        accounting_stop_query_alt = "INSERT into ${acct_table2} \
                (AcctSessionId, AcctUniqueId, UserName, Realm, NASIPAddress, NASPortType, CiscoNASPort, AcctStartTime, AcctStopTime, \
                AcctSessionTime, AcctInputOctets, AcctOutputOctets, CalledStationId, CallingStationId, \
                AcctTerminateCause, FramedProtocol, FramedIPAddress, AcctStopDelay) \
                values('%{Acct-Session-Id}', '%{Acct-Unique-Session-Id}', '%{SQL-User-Name}', '%{Realm}', '%{NAS-IP-Address}', \
                '%{NAS-Port-Type}', NULLIF('%{Cisco-NAS-Port}', ''), (now() -  '%{Acct-Delay-Time:-0}'::interval - '%{Acct-Session-Time:-0}'::interval), \
                (now() - '%{Acct-Delay-Time:-0}'::interval), NULLIF('%{Acct-Session-Time}', '')::bigint, \
                (('%{Acct-Input-Gigawords:-0}'::bigint << 32) + '%{Acct-Input-Octets:-0}'::bigint), \
                (('%{Acct-Output-Gigawords:-0}'::bigint << 32) + '%{Acct-Output-Octets:-0}'::bigint), '%{Called-Station-Id}', \
                '%{Calling-Station-Id}', '%{Acct-Terminate-Cause}', '%{Framed-Protocol}', \
                NULLIF('%{Framed-IP-Address}', '')::inet, '%{Acct-Delay-Time:-0}')"


.. NOTE:: Remember to set the ``$INCLUDE  ${confdir}/postgresql.conf`` statement
          in ``radiusd.conf``, it defaults to ``sql.conf`` which is the MySQL module.



<path to freeradius>/etc/raddb/radiusd.conf
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We noticed how some sessions' ``Acct-Unique-Session-Id`` field changed
mid-session without any apparent reason. We found that some NAS-es had an
``Acct-Session-Id`` field containing, among other data, the session's starting
time. This starting time, for some strange strange reason that we're unaware
of, sometimes change, mid-session, by a second or two, causing
``Acct-Unique-Session-Id`` to also change, since it is a hash of
``Acct-Session-Id``, among others. This small routine (or whatever the correct
naming is) strips the date and time out of ``Acct-Session-Id``.

It needs to be defined in the main section, ie. among the other
``attr_rewrite`` examples, and called in the ``preacct{}`` section, before
``acct_unique`` (which generates the unique session id). The regexp isn't very
precise, but it does the job::

  attr_rewrite modify_acctsessionid {
          attribute = Acct-Session-Id
          searchin = packet
          searchfor = "[0-3][0-9]\/[0-3][0-9]\/[0-9]{2}\ [0-2][0-9]\:[0-5][0-9]\:[0-5][0-9]"
          replacewith = ""
          append = no
  }

Also add a line saying ``sql`` to the ``accounting{}`` section. We have put it
last, but we have also seen people recommending it being put between ``unix``
and ``radutmp``, although the reason was unclear. We've experienced no known
problems by putting it last.


Step 2: Configuring your switches
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To get accounting data from your 802.1X Cisco switches, they must be
configured using the following::

  aaa accounting dot1x default start-stop group radius
  radius-server vsa send accounting


Step 3: Configuring the accounting module
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Edit ``radius_config.py``, change the values according to your setup. You
should probably only have to change ``REAUTH_TIMEOUT`` to reflect the
reauthentication interval on your FreeRADIUS server. The time is given as a
number of seconds. This value is used in the search results to indicate
whether a session is likely to still be active, or if it has timed out and not
sent an explicit *Stop*.


Step 4: Finishing up
^^^^^^^^^^^^^^^^^^^^

Restart FreeRADIUS, and you should be good to go.


Installing the error log module
-------------------------------

Step 1: Configuring the database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Edit ``pg_hba.conf`` on the database server to allow connections from the
FreeRADIUS server.

Step 2: Installing and starting the parsing script on the radius server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Edit the variables at the top of
``</path/to/radius_module/src>/radiusparser.py`` to reflect the hostname of
the NAV database server, the username and password you want for connecting to
the database, and the path to the FreeRADIUS log file, ``radius.log``.

Copy the script to a location of your choice on the server where the
``radius.log`` is accessible as part of the file system. Create a cron job
that executes this script as often as you would like to make sure that the
script is actually running. For example::

  0 * * * *  /path/to/radiusparser

This will run the script every hour, but if it detects that it is already
running, it quits and leaves the running script alone.

Of course, you may also simply execute the script yourself by running it at the
command line.


Step 3: Configuring the error log module
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Edit ``radius_config.py``, change the values according to your setup. Not much
should need to be changed here, except perhaps the ``ACCT_TABLE`` variable, if
you have chosen a different name than the default.


Setting up deletion of old entries
----------------------------------

You probably don't want the entries in the error log table or the
accounting log table accumulating forever.  To arrange for periodic
deletion of old records, create a cron snippet in NAV's ``etc/cron.d/``
directory called ``radiusclean`` and add the following lines to it::

  50 5 * * 6 /path/to/navclean --radiusacct -E "3 months" -f
  45 5 * * 6 /path/to/navclean --radiuslog  -E "1 month" -f

To insert the cron snippet into `navcron`'s crontab, run::

  sudo nav start radiusclean

This will run the ``navclean`` program once a week, deleting all radius
accounting entries older than three months and all radius error log entries
older than one month.  Feel free to change the intervals to something you
think is suitable for your organization.


Configuring NAV
---------------

Alternate configuration for differentiated db-users
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Note that this step is entirely optional.

Everything should already be configured during the installation, but it might
be desirable to have separate users for SELECT queries and queries that
updates the table (INSERT, DELETE, UPDATE). This is up to you to decide.
This will require that you create two new users in your db and do some
modifications of these files:

* ``db.conf``
* ``postgresql.conf``
* ``radius.py``
* ``radius_config.py``

Make two new entries in ``db.conf``::

  script_radius_front = <db user with SELECT privilege>
  script_radius_back = <db user with INSERT, UPDATE, DELETE privileges>

``postgresql.conf`` is the same file that is mentioned in `Step 1: Configuring
FreeRADIUS`_. Change ``login`` here to whatever you called your user with
write-privileges. See ``radius.py`` and ``radius_config.py`` for what to
change there.

