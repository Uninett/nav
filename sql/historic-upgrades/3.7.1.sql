/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.7.0 to 3.7.1.
 *
 * Connect to PostgreSQL as the postgres superuser like this:
 *
 *  psql -f 3.7.1.sql nav postgres
 *
 * Or more likely, like this:
 *
 *  sudo -u postgres psql -f 3.7.1.sql nav
 *
*/

BEGIN;
-- Insert schema changes here.

-- Ensure that deletes/updates cascades to accountalertqueue, or some
-- netboxes can't be deleted until the alert queues have been purged.
ALTER TABLE accountalertqueue DROP CONSTRAINT accountalertqueue_alert_id_fkey;
ALTER TABLE accountalertqueue ADD CONSTRAINT accountalertqueue_alert_id_fkey
    FOREIGN KEY(alert_id) REFERENCES alertq(alertqid)
    ON DELETE CASCADE ON UPDATE CASCADE;

-- Insert the new version number if we got this far.
INSERT INTO nav_schema_version (version) VALUES ('3.7.1');

COMMIT;
