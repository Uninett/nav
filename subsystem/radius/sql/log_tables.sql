CREATE TABLE uit_radiuslog (
        ID                      BIGSERIAL PRIMARY KEY,
        Time                    TIMESTAMP with time zone,
        Type                    VARCHAR(10),
        Message                 VARCHAR(170),
        Status                  VARCHAR(60),
        UserName                VARCHAR(64),  -- Not sure if this is enough
        Client                  VARCHAR(65),
        Port                    VARCHAR(8)
        );


-- To allow searching the database
--GRANT SELECT ON uit_radiuslog TO nav;

-- Indices
CREATE INDEX uit_radiuslog_time_index ON uit_radiuslog(time);
CREATE INDEX uit_radiuslog_username_index ON uit_radiuslog(username);
