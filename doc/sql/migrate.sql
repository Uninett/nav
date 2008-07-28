/*

   This script migrates dumps of NAV databases into a unified, multi-schema
   database.  Before running it, dumps must be made somewhat like this:

    su postgres 
    for DB in manage navprofiles logger arnold
      do pg_dump -f $DB-dump.sql --schema=public --no-owner --verbose --no-acl $DB
    done

   Note: This will not preserve any special table privileges you have set, as
   the ACLs are not dumped.

   This script should be run by the postgres superuser.
*/

-- Create the nav user
CREATE USER nav WITH NOCREATEDB NOCREATEUSER;

-- Create the database
CREATE DATABASE nav WITH OWNER = nav ENCODING = 'UTF-8';

-- Add the pl/pgsql language to the database
-- FIXME: Pure SQL might not be the right way to do it :P
\c nav
CREATE FUNCTION plpgsql_call_handler() RETURNS language_handler
    AS '$libdir/plpgsql', 'plpgsql_call_handler'
    LANGUAGE c;
CREATE TRUSTED PROCEDURAL LANGUAGE plpgsql HANDLER plpgsql_call_handler;

-- Make nav own the public schema.  We do this so the nav user has access to
-- alter the public namespace.
ALTER SCHEMA public OWNER TO nav;

---- An alternative pre-PostgreSQL-8.0 way to change the schema owner:
-- UPDATE pg_namespace
-- SET nspowner = (SELECT usesysid FROM pg_user WHERE usename = 'nav')
-- WHERE nspname = 'public';

-- Work as the nav user
SET SESSION AUTHORIZATION 'nav';
SET client_min_messages = warning;

-- Restore the manage dump into the `public` schema, rename it to `manage` and
-- create a new `public` schema
\i manage-dump.sql
ALTER SCHEMA public RENAME TO manage;
CREATE SCHEMA public;

-- Restore the navprofiles dump into the `public` schema, rename it to
-- `profiles` and create a new `public` schema
\i navprofiles-dump.sql
ALTER SCHEMA public RENAME TO profiles;
CREATE SCHEMA public;

-- Restore the logger dump into the `public` schema, rename it to `logger` and
-- create a new `public` schema
\i logger-dump.sql
ALTER SCHEMA public RENAME TO logger;
CREATE SCHEMA public;

-- Restore the arnold dump into the `public` schema, rename it to `arnold` and
-- create a new `public` schema
\i arnold-dump.sql
ALTER SCHEMA public RENAME TO arnold;
CREATE SCHEMA public;

ALTER DATABASE nav SET search_path = manage,profiles,logger,arnold;
\c nav

\echo Your old NAV databases were not dropped, in case you still want them for
\echo something.  You can delete them manually when they are no longer needed,
\echo by issuing these SQL statements as the postgres superuser:
\echo
\echo  DROP DATABASE manage;
\echo  DROP DATABASE navprofiles;
\echo  DROP DATABASE logger;
\echo  DROP DATABASE arnold;
