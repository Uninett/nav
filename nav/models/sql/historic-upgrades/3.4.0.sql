/*
 *
 * This preliminary SQL script is designed to upgrade your NAV database from
 * version 3.3 to the current trunk revision.  Please update this with every
 * change you make to the database initialization scripts.  It will eventually
 * become the update script for the next release.
 *
 * Also, if you are keeping your installation in sync with trunk, you should
 * watch this file for changes and run them when updating (check the diffs!)
 *
 * Connect to PostgreSQL as the postgres superuser or the nav database user
 * like this:
 *
 *  psql -f trunk.sql manage <username>
 *
*/

-- Clean install of 3.3.0 caused this rule never to be created.  Recreate it
-- here for those who started out with clean 3.3.0 installs.
-- NAV 3.3.1 also contained bug SF#1899431 in this rule, which has
-- been fixed here, and should be applied when upgrading.
CREATE OR REPLACE RULE close_arp_prefices AS ON DELETE TO prefix
  DO UPDATE arp SET end_time=NOW(), prefixid=NULL 
     WHERE prefixid=OLD.prefixid AND end_time='infinity';

-- Replace the netboxid_null_upd_end_time trigger, which has been
-- faulty the last six years.
CREATE OR REPLACE FUNCTION netboxid_null_upd_end_time () RETURNS trigger AS
  'BEGIN
     IF old.netboxid IS NOT NULL AND new.netboxid IS NULL 
        AND new.end_time = ''infinity'' THEN
       new.end_time = current_timestamp;
     END IF;
     RETURN new;
   end' LANGUAGE plpgsql;

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

-- Allow authenticated users access to the ipdevinfo tool
UPDATE accountgroupprivilege SET target = '^/(preferences|status|navAdmin|report|browse|stats|cricket|machinetracker|ipinfo|l2trace|logger|alertprofiles|ipdevinfo)/?' WHERE target = '^/(preferences|status|navAdmin|report|browse|stats|cricket|machinetracker|ipinfo|l2trace|logger|alertprofiles)/?';
