/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.6.0b1 or 3.6.0b2 to 3.6.0b3.
 *
 * Connect to PostgreSQL as the postgres superuser like this:
 *
 *  psql -f 3.6.0b3.sql nav postgres
 *
 * Or more likely, like this:
 *
 *  sudo -u postgres psql -f 3.6.0b3.sql nav
 *
*/

BEGIN;
-- Insert schema changes here.

-- View for listing all IP addresses that appear to be alive at the moment.
CREATE OR REPLACE VIEW manage.live_clients AS
  SELECT arp.ip, arp.mac
    FROM arp
   WHERE arp.end_time = 'infinity';

-- Drop trigger that causes spurious deadlocks
DROP TRIGGER update_netbox_on_prefix_changes ON prefix;
DROP FUNCTION update_netbox_prefixes();

-- Since we are running as the postgres superuser, we've just created a bunch
-- of new relations owned by postgres, and not by the current database owner.
-- This finds any relation in the NAV namespaces that is owned by the postgres
-- superuser, and resets their ownership to the database owner.
UPDATE pg_class
   SET relowner = (SELECT datdba FROM pg_database  WHERE datname=current_database())
 WHERE relowner = (SELECT usesysid
                   FROM pg_user
		   WHERE usename='postgres' AND 
		         relnamespace IN (SELECT oid 
			                  FROM pg_namespace 
					  WHERE nspname IN ('manage', 'arnold', 'logger', 'radius', 'profiles')));

-- Insert the new version number if we got this far.
INSERT INTO nav_schema_version (version) VALUES ('3.6.0b3');

COMMIT;
