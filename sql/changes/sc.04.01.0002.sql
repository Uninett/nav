-- Tested: Should not do anything bad other than print errors if run several times.

-- Add field data to org
ALTER TABLE org ADD COLUMN data hstore;

-- Copy all information from opt-fields to hstore
UPDATE org SET data = ('opt1' => opt1) || ('opt2' => opt2) || ('opt3' => opt3);

-- Drop useless opt columns
ALTER TABLE org DROP COLUMN opt1, DROP COLUMN opt2, DROP COLUMN opt3;

