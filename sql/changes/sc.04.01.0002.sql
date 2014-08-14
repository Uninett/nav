-- Tested: Should not do anything bad other than print errors if run several times.

-- Add field data to org
ALTER TABLE org ADD COLUMN data hstore;

-- Copy all information from opt-fields to hstore
UPDATE org SET data = hstore('opt1', opt1) WHERE COALESCE(opt1, '') <> '';
UPDATE org SET data = data || hstore('opt2', opt2) WHERE COALESCE(opt2, '') <> '';
UPDATE org SET data = data || hstore('opt3', opt3) WHERE COALESCE(opt3, '') <> '';

-- Drop useless opt columns
ALTER TABLE org DROP COLUMN opt1, DROP COLUMN opt2, DROP COLUMN opt3;

