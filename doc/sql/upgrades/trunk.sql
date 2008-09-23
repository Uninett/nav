/*
 *
 * This preliminary SQL script is designed to upgrade your NAV
 * database from version 3.4 to the current trunk revision (i.e. the
 * tip of the default development branch).  Please update this with
 * every change you make to the database initialization scripts.  It
 * will eventually become the update script for the next release.
 *
 * *************** NB NB NB NB NB NB NB ***************
 *
 * This upgrade scripts assumes you have merged your NAV databases
 * into a single, multi-namespaced database.  If you haven't, please
 * read the instructions in doc/sql/upgrades/README .  A helper script
 * exists to help you merge your databases: doc/sql/mergedb.sh .
 *
 * *************** NB NB NB NB NB NB NB ***************
 *
 * If you are keeping your installation in sync with the default
 * branch, you should watch this file for changes and run them when
 * updating (check the diffs!)
 *
 * Connect to PostgreSQL as the postgres superuser or the nav database user
 * like this:
 *
 *  psql -f trunk.sql nav <username>
 *
*/

-- Rename logger tables to avoid naming confusion with manage schema.
ALTER TABLE logger.message RENAME TO log_message;
ALTER SEQUENCE logger.message_id_seq RENAME TO log_message_id_seq;
ALTER INDEX logger.message_pkey RENAME TO log_message_pkey;
ALTER INDEX logger.message_origin_hash RENAME TO log_message_origin_hash;
ALTER INDEX logger.message_time_btree RENAME TO log_message_time_btree;
ALTER INDEX logger.message_type_hash RENAME TO log_message_type_hash;

ALTER TABLE logger.type RENAME TO log_message_type;
ALTER SEQUENCE logger.type_type_seq RENAME TO log_message_type_type_seq;
ALTER INDEX logger.type_priority_key RENAME TO log_message_type_priority_key;

-- combined index for quick lookups when expiring old records.
CREATE INDEX log_message_expiration_btree ON logger.log_message USING btree(newpriority, time);

-- Drop obsolete vlanPlot tables
DROP TABLE vp_netbox_xy;
DROP TABLE vp_netbox_grp;
DROP TABLE vp_netbox_info;
