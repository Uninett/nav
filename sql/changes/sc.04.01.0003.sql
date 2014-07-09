-- Ensure the data field of org and room can't be a NULL value. An empty
-- hstore value is acceptable.
UPDATE org SET data = hstore('') WHERE data IS NULL;
ALTER TABLE org ALTER COLUMN data SET NOT NULL;
ALTER TABLE org ALTER COLUMN data SET DEFAULT hstore('');

UPDATE room SET data = hstore('') WHERE data IS NULL;
ALTER TABLE room ALTER COLUMN data SET NOT NULL;
ALTER TABLE room ALTER COLUMN data SET DEFAULT hstore('');
