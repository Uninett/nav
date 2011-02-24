Getting started with NAV
========================
(This guide assumes NAV is installed in /usr/local/nav and that your
web interface is reachable at http://example.org/ )

Configuring NAV
===============
All configuration files are located below /usr/local/nav/etc/.
Default configuration files are placed here on your first install.
Most of these are documented with comments, so check each config file
to see if there's any defaults you'd like to change.

We recommend you at least change these two options in nav.conf before
running NAV:

ADMIN_MAIL 
  Should be set to the NAV administrator's e-mail address.  Any cron
  mail or other administrative e-mails from NAV will be sent to this
  address.

DOMAIN_SUFFIX
  The DNS domain name your devices are in.  Many parts of the web
  interface will chop off this suffix to display abbreviated device
  names.

Starting NAV
============
NAV has two parts; one web frontend, and a backend consisting of
multiple processes.  While Apache serves the frontend, the backend
processes can be controlled using the nav command
(/usr/local/nav/bin/nav).

The backend processes consist of some daemon processes, and some cron
jobs.  Running `nav start` will start all the daemon processes in the
background, and install all the cron jobs in the navcron user's
crontab.

The `nav start` command should be set up to be run at system boot
time.


Logging in to the web interface
===============================
When browsing the web interface at http://example.org/ you will see
the front page of NAV.  This is openly accessible to anonymous users
by default.  

To log in as an administrator, click the `Login` link and enter the
username 'admin' and the password 'admin'.  Then click the `Userinfo`
link and change the adminstrator's password to something more
sensible.


Managing accounts, groups and privileges in the web interface
=============================================================
All this is accomplished through the Useradmin panel, which should be
linked from the navigation bar of the admin user. 

Adding any user to the "NAV Administrators" group will give that user
the same level of privileges as the admin user itself.  It is
recommended to have personal accounts, even for administrators.

Seeding your database
=====================
NAV will not autodiscover your network.  You need to use the SeedDB
tool (found in the Toolbox) to seed the database with IP addresses and
SNMP communities to monitor.
