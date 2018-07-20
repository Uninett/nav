-- drop the mandatory netbox relation to device
ALTER TABLE netbox
    ALTER COLUMN deviceid DROP NOT NULL,
    DROP CONSTRAINT netbox_deviceid_key;
