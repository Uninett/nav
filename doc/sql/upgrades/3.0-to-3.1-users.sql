-- This SQL script is to convert a NAV database setup using the
-- manage/navread/navwrite users to the new recommended setup with only one
-- single `nav` user.  It should be suitable for both PostgreSQL versions 7.4
-- and 8.

-- Run the script as the postgres superuser

-- This script is distributed in the hope that it will be useful, but WITHOUT
-- ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
-- FITNESS FOR A PARTICULAR PURPOSE.  For all we know, it might wipe out your
-- hard drive, set fire to your house and run off with your wife.  If your
-- setup is not as described above, do not run this script.  Always *BACKUP*
-- your database before doing automatic schema changes.

-- Author: Alan Smithee

\c template1

-- Create the new nav user
CREATE USER nav WITH NOCREATEDB NOCREATEUSER;

-- Make this user the owner of the three databases that NAV used prior to
-- version 3.1.
UPDATE pg_database
SET datdba = (SELECT usesysid FROM pg_user WHERE usename = 'nav')
WHERE datname IN ('manage', 'navprofiles', 'logger');

-- Reset privileges on all relations in each database
\c manage
UPDATE pg_class 
SET relacl = NULL,
    relowner = (SELECT usesysid FROM pg_user WHERE usename = 'nav')
WHERE relnamespace = (SELECT oid FROM pg_namespace WHERE nspname='public');

\c navprofiles
UPDATE pg_class 
SET relacl = NULL,
    relowner = (SELECT usesysid FROM pg_user WHERE usename = 'nav')
WHERE relnamespace = (SELECT oid FROM pg_namespace WHERE nspname='public');

\c logger
UPDATE pg_class 
SET relacl = NULL,
    relowner = (SELECT usesysid FROM pg_user WHERE usename = 'nav')
WHERE relnamespace = (SELECT oid FROM pg_namespace WHERE nspname='public');


-- Now, drop all the old, silly NAV users:
\c template1
DROP USER manage;
DROP USER navread;
DROP USER navwrite;


\echo Now you should alter the password of the nav account.
\echo Do it by issuing the SQL command:
\echo '  ALTER USER nav WITH PASSWORD \'yourpasswordhere\''
\echo Don't forget to alter db.conf before starting NAV.
