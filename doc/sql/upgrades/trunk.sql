/*
 *
 * This preliminary SQL script is designed to upgrade your NAV database from
 * version 3.6.0b1 to the current trunk revision (i.e. the tip of the default
 * development branch).  Please update this with every change you make to the
 * database initialization scripts.  It will eventually become the update
 * script for the next release.
 *
 * If you are keeping your installation in sync with the default branch, you
 * should watch this file for changes and run them when updating (check the
 * diffs!).  We also recommend running navschema.py on each schema upgrade,
 * to ensure that your database's search path is alway up to date.
 *
 * Connect to PostgreSQL as the postgres superuser like this:
 *
 *  psql -f trunk.sql nav postgres
 *
 * Or more likely, like this:
 *
 *  sudo -u postgres psql -f trunk.sql nav
 *
*/

BEGIN;
-- Insert schema changes here.

-- View for listing all IP addresses that appear to be alive at the moment.
CREATE OR REPLACE VIEW manage.live_clients AS
  SELECT arp.ip, arp.mac
    FROM arp
   WHERE arp.end_time = 'infinity';

-- Insert the new version number if we got this far.
-- INSERT INTO nav_schema_version (version) VALUES ('3.6.0b1');

COMMIT;
