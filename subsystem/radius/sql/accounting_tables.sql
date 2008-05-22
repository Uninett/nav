CREATE TABLE uit_radiusacct (
        RadAcctId               BIGSERIAL PRIMARY KEY,
        AcctSessionId           VARCHAR(96) NOT NULL,
        AcctUniqueId            VARCHAR(32) NOT NULL,
        UserName                VARCHAR(32),
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


-- Freeradius ends up doing a *lot* of UPDATE queries on the database, so we 
-- need to make an index on the acctuniqueid-field, which is the field being 
-- looked up by freeradius:
CREATE INDEX uit_radiusacct_acctuniqueid_index ON uit_radiusacct (acctuniqueid);

-- Other indices that will speed up searches quite a bit:
CREATE INDEX uit_radiusacct_lower_username_index ON uit_radiusacct(lower(username));
CREATE INDEX uit_radiusacct_lower_realm_index ON uit_radiusacct(lower(realm));
CREATE INDEX uit_radiusacct_nasipaddress_index ON uit_radiusacct(nasipaddress);
CREATE INDEX uit_radiusacct_framedipaddress_index ON uit_radiusacct(framedipaddress);
CREATE INDEX uit_radiusacct_acctstarttime_index ON uit_radiusacct(acctstarttime);
CREATE INDEX uit_radiusacct_acctstoptime_index ON uit_radiusacct(acctstoptime);

-- VERY specific index, drastically speeds up the part of the search query where
-- we check if the stoptime is NULL
CREATE INDEX uit_radiusacct_acctstoptime_is_null_index ON uit_radiusacct(acctstoptime) WHERE acctstoptime IS NULL;

-- Not sure if this gets used, need to do some more testing:
CREATE INDEX uit_radiusacct_acctsessionsum_index ON uit_radiusacct(acctstarttime + (acctsessiontime * interval '1 sec')) WHERE acctstoptime IS NULL;
