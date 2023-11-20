========
 Radius
========

:Authors: Roger Kristiansen <roger.kristiansen@gmail.com>,
          Kai Bjørnenak <kai.bjornenak@cc.uit.no>
:Created: Aug. 4, 2005
:Last changed: May 23, 2008

The Radius tool makes FreeRADIUS accounting logs browseable and searchable.
It consists of a backend to log accounting data directly from FreeRADIUS into
NAV's PostgreSQL database, and a frontend to browse/search the data on the
web.

Files
=====

.. WARNING:: This following file listing seems to bit somewhat out of date.

========================= =======================================================
doc/README.txt            What you are probably reading right now :]
doc/INSTALL.txt           How to install the radius accounting subsystem

bin/navclean              Modified version of navclean.py, that also handles
                          the radius accounting table. Should probably me made
                          to also handle the log table, or dropped all together.
bin/radiusparser          radius.log parser that inserts data into the database.

sql/accounting_table.sql  Script for creating the accounting table
sql/log_table.sql         Script for creating the log table
sql/users.sql             Script for creating the users needed for the modules
                          to work.

AcctChartsTemplate.tmpl   Cheetah Template for the accounting upload/download
                          charts.
AcctChartsTemplate.py     Module compiled from AcctChartsTemplate.tmpl
AcctSearchTemplate.tmpl   Template for the accounting search page.
AcctSearchTemplate.py     Module compiled from AcctChartsTemplate.tmpl
AcctDetailTemplate.tmpl   Template for the accounting session details page.
AcctDetailTemplate.py     Module compiled from AcctDetailTemplate.tmpl
LogTemplate.tmpl          Template for the error log search page.
LogTemplate.py            Module compiled from LogTemplate.tmpl
LogDetailTemplate.tmpl    Template for the error log details page.
LogDetailTemplate.py      Module compiled from LogDetailTemplate.tmpl
radius.py                 The handler, and a few classes for performing SQL
                          queries, and some Exception classes
radiuslib.py              A few helper functions used throughout the templates
radius_config.py          Configuration variables
radius.tool               Entry for NAV's menu system
.htaccess                 Apache .htaccess file, setting up handler etc.
========================= =======================================================


About
=====

This module was made by someone not too familiar with Python, and who had never
touched either NAV or Cheetah before the project started. If you see something
that seems awkward, don't hesitate to suggest a better way to do it.

It should be pretty obvious that we have ripped extensively from NAV's
MachineTracker subsystem, and at the time writing this, even the graphics in the
tables are from MachineTracker.

There have yet to be confirmed reports on this stuff working (or even being
tried) on any other setup than what it was developed on, which is:

* NAV v3.3.3
* PostgreSQL 7.4.8
* Python 2.4

Please tell us about successful installs on other setups.


Installation
============

See :doc:`separate installation instructions <radius-install>` for
configuring your FreeRADIUS server to log accounting data to NAV.


Usage
=====

The visual part of the Radius accounting subsystem consists of 3 main sections;
a search page, a page for displaying details about a specific session, a
page top users in terms of traffic and a search page for the error log.


Search page
-----------

Hopefully it will be pretty self explanatory. You choose your search criteria
and click the search button. The sessions that get matched are all sessions
that "touch" your specified time interval in any way. At the bottom of the
page, you will get a summary for your search, giving you the total amount of
uploaded/downloaded data for all sessions matching your search criterias. This
feature is currently made a bit useless from the duplicate sessions in the
database (see `Known Issues`_).

In the search results, you will sometimes see sessions whose `Session Stop`
field contains text in stead of the actual stop time. Here is an explanation
of what they mean:

"Still Active"
  This doesn't guarantee 100% that this session is still active, but it does
  mean that the session has not yet timed out and that the radius server is
  waiting for reauthentication/confirmation for this session.

"Timed Out"
  This means that the session was abandoned without any
  explicit stop message reaching the radius server, and that the server
  no longer considers this session active.

For this feature to work correctly, the variable ``REAUTH_TIMEOUT`` in
``radius_config.py`` must be set correctly

There are links from `Username`, `Realm`, `Assigned IP` and `NAS IP`
to new searches. I.e. clicking on a username will show all sessions for this
user, using the already specified time interval. A click on a session id will
bring up all available details for that session.

Take care when searching for large time intervals, so you don't trash your
DB server.


Details page
------------

Displays all the details about a session, as specified in the list called
``LOG_DETAILSFIELDS`` in ``radius_config.py``.


Charts page
-----------

Displays top upload, top download, and top overall bandwidth hog for as many
days back as the user specifies. The default is a week (7 days).

This chart will lie a little, since it sums up all sessions that ended within
the specified number of days. The reason for doing this is that we only get any
numbers on how much data the user has sent/received when the session ends. Thus
there is really no way to know for sure, just from the radius accounting log,
when during the session the data was transferred.

Of course, we could always limit the search to sessions that only started
inside our search interval, but then a lot of long sessions might slip under
the radar.




Making Changes
==============

If you want to make changes in the html, you will have to edit the corresponding
``.tmpl`` file, and make a python module of it with ``cheetah c <templatename>``.




Known Issues
============

Accounting module: Duplicate entries for some sessions
------------------------------------------------------

Sometimes, when a Start message is immediately followed by an Alive message for
the same session, FreeRADIUS inserts the session into the database twice, the
only difference between them seem to be a few hundreds of a second on the Start
time. This seems to be caused by the following scenario:

1) FreeRADIUS receives a Start packet and inserts a new entry/session in the db
2) FreeRADIUS receives an Alive packet for the same session *immediately* after
   the Start packet, and queries the database to see if the `unique-session-id`
   already exists.
3) The query doesn't return anything, since postgresql hasn't had time to
   complete the `INSERT`-query for the Start packet, and
   ``accounting_update_query_alt`` is thus run, inserting a new row.

How to get around this? I'm not quite sure. Maybe someone with more experience
with (Postgre)SQL could look at some kind of table locking, if this wouldn't
slow down the server too much. Another solution suggested by one of
FreeRADIUS' developers was using ``rlm_sql_log`` in FreeRADIUS to output a
file with SQL queries, and post-processing them. I haven't had the time to
play around with any of this.



FreeRADIUS encoding
-------------------

This module does not handle FreeRADIUS' way of encoding characters with
`UTF-8` gracefully. Norwegian characters `ÆØÅ` and cyrilic characters get
replaced by their octal representation on the form ``\xxx\xxx``. To give an
example the octal representation ``\303\246`` is the norwegian character
`æ`. I suspect this bug also affects characters with accents and other special
characters.




TODO
====

* Create useful links to other parts of NAV or new searches. Feedback on
  how people use the information on this page would be useful for knowing what
  to link to.

