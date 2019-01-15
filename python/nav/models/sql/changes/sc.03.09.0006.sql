-- Fix broken constraint on rrd_file
DELETE FROM rrd_file WHERE netboxid IS NULL;
ALTER TABLE rrd_file DROP CONSTRAINT rrd_file_netboxid_fkey;
ALTER TABLE rrd_file ADD CONSTRAINT rrd_file_netboxid_fkey
  FOREIGN KEY (netboxid) REFERENCES netbox(netboxid)
  ON UPDATE CASCADE ON DELETE CASCADE;
