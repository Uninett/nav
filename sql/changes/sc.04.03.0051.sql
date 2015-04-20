--- Remove unique constraints for module table

ALTER TABLE module DROP CONSTRAINT IF EXISTS module_deviceid_key;
ALTER TABLE module DROP CONSTRAINT IF EXISTS module_netboxid_key;
