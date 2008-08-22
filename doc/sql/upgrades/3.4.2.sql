/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.4.0 or 3.4.1 to 3.4.2.  
 *
 * This script is only necessary if either:
 *
 * 1. You installed NAV 3.4 from scratch, creating a new database.
 *
 *  or
 *
 * 2. You installed NAV on a PostgreSQL version 8.3 database.
 *
 *
 * NAV 3.4.1 and 3.4.1 were shipped with a manage.sql containing a
 * couple of errors in the order of which relations and rules were
 * created, and also a small typecasting error only present on
 * PostgreSQL 8.3 and newer (See SF#2023345 for more details).
 *
 *
 * Run the script as the nav database user like this:
 *
 *  psql -f 3.4.2.sql manage nav
 *
*/

BEGIN;

-- Redefine these two rules to make sure that they actually are
-- present.
CREATE OR REPLACE RULE netbox_close_arp AS ON DELETE TO netbox
  DO UPDATE arp SET end_time=NOW()
     WHERE netboxid=OLD.netboxid AND end_time='infinity';

CREATE OR REPLACE RULE netbox_close_cam AS ON DELETE TO netbox
  DO UPDATE cam SET end_time=NOW()
     WHERE netboxid=OLD.netboxid AND end_time='infinity';


-- Redefine this rule to make sure it is present also on a PostgreSQL
-- 8.3 database.
CREATE OR REPLACE RULE rrdfile_deleter AS
    ON DELETE TO service
    DO DELETE FROM rrd_file
        WHERE key='serviceid' AND value=old.serviceid::text;

COMMIT;
