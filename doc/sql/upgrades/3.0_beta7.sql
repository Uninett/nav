/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.0_beta6 to 3.0_beta7.  Connect to PostgreSQL as the
 * postgres superuser and run this script like this:
 *
 * psql -f 3.0_beta7.sql manage postgres
 *
 * Please, also run the updated snmpoid.sql script over again, like
 * this:
 *
 * psql -f snmpoid.sql manage postgres
 *
 * *!IMPORTANT!* The Syslog Analyzer has been reimplemented in this
 * release, and you must follow the procedure from the doc/sql/README
 * file to create the logger database, or you new NAV version will not
 * work.
 *
*/

\c manage

BEGIN;
DROP TABLE port2off;

CREATE TABLE cabling (
  cablingid SERIAL PRIMARY KEY,
  roomid VARCHAR(30) NOT NULL REFERENCES room ON UPDATE CASCADE ON DELETE CASCADE,
  jack VARCHAR NOT NULL,
  building VARCHAR NOT NULL,
  targetroom VARCHAR NOT NULL,
  descr VARCHAR,
  category VARCHAR NOT NULL,
UNIQUE(roomid,jack));

CREATE TABLE patch (
  patchid SERIAL PRIMARY KEY,
  swportid INT4 NOT NULL REFERENCES swport ON UPDATE CASCADE ON DELETE CASCADE,
  cablingid INT4 NOT NULL REFERENCES cabling ON UPDATE CASCADE ON DELETE CASCADE,
  split VARCHAR NOT NULL DEFAULT 'no',
UNIQUE(swportid,cablingid));

ALTER TABLE vp_netbox_grp_info ADD COLUMN hideicons BOOL;
ALTER TABLE vp_netbox_grp_info ALTER COLUMN hideicons SET DEFAULT false;
UPDATE vp_netbox_grp_info SET hideicons=false where hideicons IS NULL;
ALTER TABLE vp_netbox_grp_info ALTER COLUMN hideicons SET NOT NULL;
ALTER TABLE vp_netbox_grp_info ADD COLUMN iconname VARCHAR;

-- Typenames were wrong for two types, fix those here
UPDATE type SET typename='catalyst297024TS' WHERE typename='c2970';
UPDATE type SET typename='catalyst37xxStack' WHERE typename='c3750';

COMMIT;


\c navprofiles
-- Fix previous typos in privilege assignment for the messages subsystem
BEGIN;
UPDATE AccountGroupPrivilege 
  SET   target='^/messages/(main\\.py|rss|historic|active|planned|view|maintenance)\\b' 
  WHERE target='^/messages/(rss|historic|active|planned|view|maintenance)\\b';

UPDATE AccountGroupPrivilege 
  SET   target='^/messages/?$'
  WHERE target='^/messages\\b';
COMMIT;



\echo **********************************************************
\echo * Have you remembered to create the new logger database? *
\echo **********************************************************
