/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.5.0b1 to 3.5.0b2
 *
 * *************** NB NB NB NB NB NB NB ***************
 *
 * This upgrade script assumes you have merged your NAV databases
 * into a single, multi-namespaced database and run 3.5.0b1.sql.  If
 * you haven't, please read the release notes for NAV 3.5 and the
 * instructions in doc/sql/upgrades/README .  
 *
 * *************** NB NB NB NB NB NB NB ***************
 *
 * Connect to PostgreSQL and run this script as the nav database owner
 * like this:
 *
 *  psql -f 3.5.0b2.sql <db_name> <username>
 *
 * When you are done, make sure the database search path is correct,
 * by running the new program navschema.py.  Otherwise your radius
 * module might not work.
*/

BEGIN;

-- Insert alert senders.
-- Conditional, in case someone already fixed their install manually.
INSERT INTO alertsender (id, name, handler) SELECT 1, 'Email', 'email'
  WHERE NOT EXISTS (SELECT id FROM alertsender WHERE id=1);

INSERT INTO alertsender (id, name, handler) SELECT 2, 'SMS', 'sms'
  WHERE NOT EXISTS (SELECT id FROM alertsender WHERE id=2);

INSERT INTO alertsender (id, name, handler) SELECT 3, 'Jabber', 'jabber'
  WHERE NOT EXISTS (SELECT id FROM alertsender WHERE id=3);

-- Fix for LP#285331 Duplicate RRD file references
-- Delete oldest entries if there are duplicate rrd file references
DELETE FROM rrd_file 
WHERE rrd_fileid IN (SELECT b.rrd_fileid
                     FROM rrd_file a
                     JOIN rrd_file b ON (a.path = b.path AND 
                                         a.filename=b.filename AND 
                                         a.rrd_fileid > b.rrd_fileid)
                     );

-- Modify rrd_file to prevent duplicate path/filename entries
ALTER TABLE rrd_file ADD CONSTRAINT rrd_file_path_filename_key UNIQUE (path, filename);

-- Tables and indices for new radius accounting subsystem
CREATE SCHEMA radius;
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

------------------------------------------------------------------------------
-- simple schema version check table
------------------------------------------------------------------------------
CREATE TABLE manage.nav_schema_version (
    version VARCHAR NOT NULL,
    time TIMESTAMP NOT NULL DEFAULT NOW()
);

-- FIXME: Insert default as version name.  This should be updated on
-- each NAV release branch.
INSERT INTO nav_schema_version (version) VALUES ('3.5.0b2');

-- Ensure only a single row will ever exist in this table.
CREATE OR REPLACE RULE nav_schema_version_insert AS ON INSERT TO nav_schema_version
    DO INSTEAD UPDATE nav_schema_version SET version=NEW.version, time=NOW();

COMMIT;