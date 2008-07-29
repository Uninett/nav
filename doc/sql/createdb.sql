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

SET SESSION AUTHORIZATION 'nav';
SET client_min_messages = warning;

-- Create schemas
CREATE SCHEMA manage;
CREATE SCHEMA profiles;
CREATE SCHEMA logger;
CREATE SCHEMA arnold;

-- Now, initialize the database
SET search_path = manage;
\i manage.sql
\i types.sql
\i snmpoid.sql

SET search_path = profiles;
\i navprofiles.sql

SET search_path = logger;
\i logger.sql

SET search_path = arnold;
\i arnold.sql

ALTER DATABASE nav SET search_path = manage,profiles,logger,arnold;
RESET search_path;

-- Build indexes now
\i indexes.sql
