-- Tested: Should not do anything bad other than print errors if run several times.

-- Add field data to room - requires the hstore extension to be installed.
ALTER TABLE room ADD COLUMN data hstore;

-- Copy all information from opt-fields to hstore
UPDATE room SET data = hstore('opt1', opt1) WHERE COALESCE(opt1, '') <> '';
UPDATE room SET data = data || hstore('opt2', opt2) WHERE COALESCE(opt2, '') <> '';
UPDATE room SET data = data || hstore('opt3', opt3) WHERE COALESCE(opt3, '') <> '';
UPDATE room SET data = data || hstore('opt4', opt4) WHERE COALESCE(opt4, '') <> '';

-- Drop useless opt columns
ALTER TABLE room DROP COLUMN opt1, DROP COLUMN opt2, DROP COLUMN opt3, DROP COLUMN opt4;

