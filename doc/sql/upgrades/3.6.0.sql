/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.6.0b6 to 3.6.0 (final).
 *
 * Connect to PostgreSQL as the postgres superuser like this:
 *
 *  psql -f 3.6.0.sql nav postgres
 *
 * Or more likely, like this:
 *
 *  sudo -u postgres psql -f 3.6.0.sql nav
 *
*/

BEGIN;
-- Insert schema changes here.

ALTER TABLE rproto_attr
  DROP CONSTRAINT rproto_attr_interfaceid_fkey;

ALTER TABLE rproto_attr
  ADD CONSTRAINT rproto_attr_interfaceid_fkey FOREIGN KEY (interfaceid) REFERENCES interface
  ON UPDATE CASCADE ON DELETE CASCADE;

-- getDeviceData may have left duplicate interfaces hanging around in
-- the database, so we try to resolve them here.  Let ipdevpoll fix
-- the rest.
DELETE FROM interface
WHERE interfaceid IN (
  SELECT
    i2.interfaceid AS dupe_id
  FROM
    interface i1
  JOIN
    interface i2 ON (i1.netboxid = i2.netboxid AND
                     i1.ifindex = i2.ifindex AND
                     i1.interfaceid > i2.interfaceid)
);

ALTER TABLE interface
  DROP CONSTRAINT interface_interfaceid_netboxid_unique;

ALTER TABLE interface
  ADD CONSTRAINT interface_netboxid_ifindex_unique UNIQUE (netboxid, ifindex);

CREATE INDEX arp_netboxid_btree ON arp USING btree (netboxid);

-- Insert the new version number if we got this far.
INSERT INTO nav_schema_version (version) VALUES ('3.6.0');

COMMIT;
