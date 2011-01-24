/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.6.0b3 or 3.6.0b4 to 3.6.0b5.
 *
 * Connect to PostgreSQL as the postgres superuser like this:
 *
 *  psql -f 3.6.0b5.sql nav postgres
 *
 * Or more likely, like this:
 *
 *  sudo -u postgres psql -f 3.6.0b5.sql nav
 *
*/
BEGIN;
-- Insert schema changes here.

ALTER TABLE netbox DROP COLUMN subcat;
ALTER TABLE netbox DROP COLUMN snmp_agent;
ALTER TABLE device DROP COLUMN auto;
ALTER TABLE "type" DROP COLUMN frequency;

-- Insert the new version number if we got this far.
INSERT INTO nav_schema_version (version) VALUES ('3.6.0b5');

COMMIT;
