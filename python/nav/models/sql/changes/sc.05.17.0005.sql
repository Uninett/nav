-- Add missing index on netboxentity.deviceid to speed up lookups by device
DROP INDEX IF EXISTS netboxentity_deviceid_btree;
CREATE INDEX netboxentity_deviceid_btree ON netboxentity (deviceid) WHERE deviceid IS NOT NULL;
