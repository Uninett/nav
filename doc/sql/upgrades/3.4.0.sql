/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.3 to 3.4.
 *
 * Run the script as the nav database user like this:
 *
 *  psql -f 3.4.0.sql manage nav
 *
 * Also make sure to run types.sql and snmpoid.sql to make sure your type and
 * snmpoid tables are up-to-date:
 *
 *  psql -f types.sql manage nav
 *  psql -f snmpoid.sql manage nav
 *
*/

\connect manage
BEGIN;

-- Clean install of 3.3.0 caused this rule never to be created.  Recreate it
-- here for those who started out with clean 3.3.0 installs.
-- NAV 3.3.1 also contained bug SF#1899431 in this rule, which has
-- been fixed here, and should be applied when upgrading.
CREATE OR REPLACE RULE close_arp_prefices AS ON DELETE TO prefix
  DO UPDATE arp SET end_time=NOW(), prefixid=NULL 
     WHERE prefixid=OLD.prefixid AND end_time='infinity';

-- Remove the netboxid_null_upd_end_time trigger, which runs on every
-- single update to arp and cam.  Replace it with two delete rules to
-- the netbox table instead.
DROP TRIGGER update_arp ON arp;
DROP TRIGGER update_cam ON cam;
DROP FUNCTION netboxid_null_upd_end_time();

CREATE OR REPLACE RULE netbox_close_arp AS ON DELETE TO netbox
  DO UPDATE arp SET end_time=NOW()
     WHERE netboxid=OLD.netboxid AND end_time='infinity';

CREATE OR REPLACE RULE netbox_close_cam AS ON DELETE TO netbox
  DO UPDATE cam SET end_time=NOW()
     WHERE netboxid=OLD.netboxid AND end_time='infinity';

-- Django needs a single column it can treat as primary key :-(
ALTER TABLE netboxcategory ADD COLUMN id SERIAL;
ALTER TABLE netbox_vtpvlan ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE netboxsnmpoid ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE serviceproperty ADD COLUMN id SERIAL;
ALTER TABLE maint_component ADD COLUMN id SERIAL;
ALTER TABLE message_to_maint_task ADD COLUMN id SERIAL;
ALTER TABLE alertqmsg ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE alertqvar ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE alerthistmsg ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE alerthistvar ADD COLUMN id SERIAL PRIMARY KEY;

-- Both old IP Device Center and new IP Device Info does lots of selects on cam
-- with netboxid and ifindex in the where clause
CREATE INDEX cam_netboxid_ifindex_end_time_btree ON cam USING btree (netboxid, ifindex, end_time);

-- RRD file values are used a lot in Netmap
CREATE INDEX rrd_file_value ON rrd_file(value);

--
-- Add field 'contact' to org-table in manage-database
--


ALTER TABLE org ADD contact VARCHAR;


END;
--
-- The following changes to the arnold-database are necessary to migrate to new version of Arnold.
--

\connect arnold
BEGIN;

-- Create new table for storing of quarantine vlans.
CREATE TABLE quarantine_vlans (
quarantineid SERIAL PRIMARY KEY,
vlan INT,
description VARCHAR
);

-- Changes regarding table blocked_reasons
ALTER TABLE blocked_reason RENAME text TO name;
ALTER TABLE blocked_reason ADD comment VARCHAR;

-- Changes regarding table identity
ALTER TABLE identity DROP CONSTRAINT identity_blocked_status_check;
ALTER TABLE identity ADD CONSTRAINT identity_blocked_status_check CHECK (blocked_status='disabled' OR blocked_status='enabled' OR blocked_status='quarantined');

ALTER TABLE identity DROP COLUMN swsysname;
ALTER TABLE identity DROP COLUMN swvendor;
ALTER TABLE identity DROP COLUMN swip;
ALTER TABLE identity DROP COLUMN swmodule;
ALTER TABLE identity DROP COLUMN swport;
ALTER TABLE identity DROP COLUMN swifindex;
ALTER TABLE identity DROP COLUMN community;
ALTER TABLE identity DROP COLUMN multiple;
ALTER TABLE identity DROP COLUMN secret;
ALTER TABLE identity DROP COLUMN userlock;

ALTER TABLE identity ADD fromvlan INT;
ALTER TABLE identity ADD tovlan INT;

-- Changes to event table
ALTER TABLE event DROP CONSTRAINT event_blocked_status_check;
ALTER TABLE event ADD CONSTRAINT event_blocked_status_check CHECK (blocked_status='disabled' OR blocked_status='enabled' OR blocked_status='quarantined');

-- Changes regarding table block
ALTER TABLE block DROP COLUMN private;
ALTER TABLE block DROP COLUMN userid;

ALTER TABLE block ADD activeonvlans VARCHAR;
ALTER TABLE block ADD detainmenttype VARCHAR CHECK (detainmenttype='disable' OR detainmenttype='quarantine');
ALTER TABLE block ADD quarantineid INT REFERENCES quarantine_vlans ON UPDATE CASCADE ON DELETE CASCADE;

END;

\c navprofiles

BEGIN;
-- Increase the maximum length of user organization IDs, to fix SF#1680011
ALTER TABLE AccountOrg ALTER COLUMN orgid TYPE VARCHAR(30);
END;
