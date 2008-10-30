/*
 *
 * This preliminary SQL script is designed to upgrade your NAV database from
 * version 3.5 to the current trunk revision (i.e. the tip of the default
 * development branch).  Please update this with every change you make to the
 * database initialization scripts.  It will eventually become the update
 * script for the next release.
 *
 * If you are keeping your installation in sync with the default branch, you
 * should watch this file for changes and run them when updating (check the
 * diffs!)
 *
 * Connect to PostgreSQL as the postgres superuser or the nav database user
 * like this:
 *
 *  psql -f trunk.sql nav <username>
 *
*/

-- Alert senders
INSERT INTO alertsender VALUES (1, 'Email', 'email');
INSERT INTO alertsender VALUES (2, 'SMS', 'sms');
INSERT INTO alertsender VALUES (3, 'Jabber', 'jabber'); 

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
