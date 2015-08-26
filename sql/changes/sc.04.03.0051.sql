--- Remove unique constraints for devices in module table

ALTER TABLE module DROP CONSTRAINT IF EXISTS module_deviceid_key;
