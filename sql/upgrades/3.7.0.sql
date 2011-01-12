/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.6.1 to 3.7.0.
 *
 * Connect to PostgreSQL as the postgres superuser like this:
 *
 *  psql -f 3.7.0.sql nav postgres
 *
 * Or more likely, like this:
 *
 *  sudo -u postgres psql -f 3.7.0.sql nav
 *
*/
BEGIN;
-- Insert schema changes here.

ALTER TABLE room ADD COLUMN position POINT;

-- Insert the new version number if we got this far.
INSERT INTO nav_schema_version (version) VALUES ('3.7.0');

COMMIT;
