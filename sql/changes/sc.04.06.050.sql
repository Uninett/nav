-- Create table for storing prefix tags
CREATE TABLE IF NOT EXISTS prefix_usage (
    prefixid INTEGER REFERENCES prefix (prefixid)
             ON UPDATE CASCADE ON DELETE CASCADE,
    usageid  VARCHAR REFERENCES usage (usageid)
             ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT prefix_usage_pkey
               PRIMARY KEY (prefixid, usageid)
);
