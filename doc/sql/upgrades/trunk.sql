/*
 *
 * This preliminary SQL script is designed to upgrade your NAV database from
 * version 3.5 to the current trunk revision (i.e. the tip of the default
 * development branch).  Please update this with every change you make to the
 * database initialization scripts.  It will eventually become the update
 * script for the next release.
 *
 * If you are keeping your installation in sync with the default branch, you
 * should watch this file for changes and run them when updating (check the
 * diffs!).  We also recommend running navschema.py on each schema upgrade,
 * to ensure that your database's search path is alway up to date.
 *
 * Connect to PostgreSQL as the postgres superuser or the nav database user
 * like this:
 *
 *  psql -f trunk.sql nav <username>
 *
*/

BEGIN;
-- Insert schema changes here.
COMMIT;
