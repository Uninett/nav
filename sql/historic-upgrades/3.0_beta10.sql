/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.0_beta9 to 3.0_beta10.
 *
 * The collection of memory information from devices has remained
 * unimplemented in NAV 3 until now, which prompted the addition of a
 * UNIQUE contraint to the mem table
 *
 * Connect to PostgreSQL as the postgres superuser and run this script
 * like this:
 *
 * psql -f 3.0_beta8.sql manage postgres
 *
 * Please, also run the updated snmpoid.sql script over again, like
 * this:
 *
 * psql -f snmpoid.sql manage postgres
 *
*/

BEGIN;
-- Make sure the table is empty before we proceed
DELETE FROM mem;
ALTER TABLE mem ADD CONSTRAINT mem_netboxid_key UNIQUE(netboxid, memtype, device);
COMMIT;
