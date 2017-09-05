-- Create table for storing prefix tags
CREATE TABLE IF NOT EXISTS manage.prefix_usage (
    prefix_usage_id SERIAL PRIMARY KEY,
    prefixid        INTEGER REFERENCES prefix (prefixid)
                    ON UPDATE CASCADE ON DELETE CASCADE,
    usageid         VARCHAR REFERENCES usage (usageid)
                    ON UPDATE CASCADE ON DELETE CASCADE,
    UNIQUE (prefixid, usageid)
);
