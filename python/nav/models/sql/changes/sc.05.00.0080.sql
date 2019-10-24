-- Ensure that the location "mylocation" exists, works on pg9.4
INSERT INTO location (locationid, descr)
    SELECT 'mylocation', 'Example location' WHERE
        NOT EXISTS (SELECT * FROM location WHERE locationid = 'mylocation');

-- Add "mylocation" to all rooms missing a location
UPDATE room SET locationid = 'mylocation' WHERE locationid IS NULL;

-- Ensure that location must alwayus exist for a room
ALTER TABLE room ALTER COLUMN locationid SET NOT NULL;
