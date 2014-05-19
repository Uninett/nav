-- Tested: Should not do anything bad other than print errors if run several times.

-- Add field data to room - requires the hstore extension to be installed.
ALTER TABLE room ADD COLUMN data hstore;

-- Copy all information from opt-fields to hstore
UPDATE room SET data = ('opt1' => opt1) || ('opt2' => opt2) || ('opt3' => opt3) || ('opt4' => opt4);

-- Drop useless opt columns
ALTER TABLE room DROP COLUMN opt1, DROP COLUMN opt2, DROP COLUMN opt3, DROP COLUMN opt4;

