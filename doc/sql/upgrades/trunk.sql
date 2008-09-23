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

-- Drop obsolete vlanPlot tables
DROP TABLE vp_netbox_xy;
DROP TABLE vp_netbox_grp;
DROP TABLE vp_netbox_info;


-- Tables and indices for new radius accounting subsystem

SET search_path TO radius;

CREATE TABLE radiusacct (
        RadAcctId               BIGSERIAL PRIMARY KEY,
        AcctSessionId           VARCHAR(96) NOT NULL,
        AcctUniqueId            VARCHAR(32) NOT NULL,
        UserName                VARCHAR(70),
        Realm                   VARCHAR(24),
        NASIPAddress            INET NOT NULL,
        NASPortType             VARCHAR(32),
        CiscoNASPort            VARCHAR(32),
        AcctStartTime           TIMESTAMP,
        AcctStopTime            TIMESTAMP,
        AcctSessionTime         BIGINT,
        AcctInputOctets         BIGINT,
        AcctOutputOctets        BIGINT,
        CalledStationId         VARCHAR(50),
        CallingStationId        VARCHAR(50),
        AcctTerminateCause      VARCHAR(32),
        FramedProtocol          VARCHAR(32),
        FramedIPAddress         INET,
        AcctStartDelay          BIGINT,
        AcctStopDelay           BIGINT
);

CREATE TABLE radiuslog (
        ID                      BIGSERIAL PRIMARY KEY,
        Time                    TIMESTAMP with time zone,
        Type                    VARCHAR(10),
        Message                 VARCHAR(200),
        Status                  VARCHAR(65),
        UserName                VARCHAR(70),
        Client                  VARCHAR(65),
        Port                    VARCHAR(8)
        );


-- For use by onoff-, update-, stop- and simul_* queries
CREATE INDEX radiusacct_active_user_idx ON radiusacct (UserName) WHERE AcctStopTime IS NULL;
-- and for common statistic queries:
CREATE INDEX radiusacct_start_user_index ON radiusacct (AcctStartTime, lower(UserName));
CREATE INDEX radiusacct_stop_user_index ON radiusacct (AcctStopTime, UserName);

CREATE INDEX radiuslog_time_index ON radiuslog(time);
CREATE INDEX radiuslog_username_index ON radiuslog(UserName);

RESET search_path;
