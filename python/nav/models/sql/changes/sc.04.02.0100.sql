-- fix ambiguity in the subid field of alert and event tables
-- as a result of LP#1403365
UPDATE eventq SET subid='' WHERE subid IS NULL;
UPDATE alertq SET subid='' WHERE subid IS NULL;
UPDATE alerthist SET subid='' WHERE subid IS NULL;

ALTER TABLE eventq ALTER COLUMN subid SET NOT NULL;
ALTER TABLE eventq ALTER COLUMN subid SET DEFAULT '';

ALTER TABLE alertq ALTER COLUMN subid SET NOT NULL;
ALTER TABLE alertq ALTER COLUMN subid SET DEFAULT '';

ALTER TABLE alerthist ALTER COLUMN subid SET NOT NULL;
ALTER TABLE alerthist ALTER COLUMN subid SET DEFAULT '';
