/*
=============================================

    SQL Initialization script for NAV's radius accounting tables.
    Read the README file for more info.
    
	!! WARNING !!

	This SQL script is encoded as unicode (UTF-8), before you do make
	changes and commit, be 100% sure that your editor does not mess it up.
    
    Check 1 : These norwegian letters looks nice:
    ! æøåÆØÅ !
    Check 2 : This is the Euro currency sign: 
    ! € !

    These table definitions are grabbed from wiki.freeradius.org and have been 
    slightly modified for use with the radius-module.

=============================================
*/

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

