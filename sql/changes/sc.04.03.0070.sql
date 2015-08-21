-- Fix data type of netboxentity.index, which, for mysterious reasons, was
-- defined as varchar in 4.3.0
ALTER TABLE netboxentity
    ALTER COLUMN index TYPE INTEGER
    USING index::INT;
