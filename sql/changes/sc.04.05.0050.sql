-- Add fields to apitoken
ALTER TABLE apitoken ADD COLUMN created TIMESTAMP DEFAULT now();
ALTER TABLE apitoken ADD COLUMN last_used TIMESTAMP;
ALTER TABLE apitoken ADD COLUMN comment TEXT;
ALTER TABLE apitoken ADD COLUMN revoked BOOLEAN default FALSE;
ALTER TABLE apitoken ADD COLUMN endpoints hstore;

UPDATE apitoken SET created = NULL;

