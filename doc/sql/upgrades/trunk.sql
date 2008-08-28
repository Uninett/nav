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
 * read the instructions in doc/sql/migrate.sql, and use that script
 * to merge your databases first.  Only then should you use this
 * script.
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

ALTER TABLE logger.type RENAME TO message_type;
ALTER SEQUENCE logger.type_type_seq RENAME TO message_type_type_seq;

-- Allow authenticated users to visit ipdevinfo
INSERT INTO accountgroupprivilege (accountgroupid, privilegeid, target)
VALUES (3, 2, '^/ipdevinfo/?');
