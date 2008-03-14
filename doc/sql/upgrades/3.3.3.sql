/*
 *
 * This SQL script is designed to fix trigger bugs in your NAV
 * database from versions older than 3.3.3.  THIS SCRIPT MAY NOT WORK
 * ON POSTGRESQL VERSIONS PRIOR TO 8.0.
 *
 * Run the script as the nav database user like this:
 *
 *  psql -f 3.3.3.sql manage nav
 *
*/

BEGIN;

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

END;
