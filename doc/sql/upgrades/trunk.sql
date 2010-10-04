/*
 *
 * This preliminary SQL script is designed to upgrade your NAV database from
 * version 3.6.0b6 to the current trunk revision (i.e. the tip of the default
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
-- INSERT INTO nav_schema_version (version) VALUES ('3.6.0b1');

COMMIT;
